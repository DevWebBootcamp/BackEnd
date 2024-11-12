from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import app.crud as crud
import app.schema as schema
import app.auth  as auth
from app.database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from sqlalchemy.exc import IntegrityError
import os, uuid, shutil
from typing import Optional
from datetime import date
from fastapi.responses import Response
from app.config import ITEM_IMAGE_DIR

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 사용자 공간 추가
@router.post("/{user_no}/spaces", response_model=schema.StorageAreaSchema, summary="사용자 공간 추가")
def create_user_storage_space(
    user_no: int, 
    storage_data: schema.StorageAreaCreate, 
    db: Session = Depends(get_db), 
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 현재 로그인한 사용자만 자신의 저장 공간을 추가할 수 있도록 제한
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to add storage space.")

    space = crud.create_storage_space(db=db, user_no=user_no, area_name=storage_data.area_name)
    return space

# 사용자 모든 공간 조회
@router.get("/{user_no}/spaces", response_model=List[schema.StorageAreaSchema], summary="사용자 모든 공간 조회")
def load_user_storage_space(
    user_no: int,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 현재 로그인한 사용자만 자신의 저장 공간에 접근할 수 있도록 제한
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to access this storage space.")
    
    spaces = crud.load_user_storage_space(db, user_no=user_no)
    return [schema.StorageAreaSchema.model_validate(space) for space in spaces] if spaces else []


# 특정 저장 공간 조회
@router.get("/{user_no}/spaces/{area_no}", response_model=schema.StorageAreaSchema, summary="특정 저장 공간 조회")
def read_user_storage_space(
    user_no: int, 
    area_no: int, 
    db: Session = Depends(get_db), 
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 현재 로그인한 사용자만 자신의 저장 공간에 접근할 수 있도록 제한
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to access this storage space.")
    
    # 특정 유저가 해당 저장 공간을 소유하는지 확인
    space = crud.get_user_storage_space(db, user_no=user_no, area_no=area_no)
    
    return space

# 사용자 공간 수정
@router.put("/{user_no}/spaces/{area_no}", response_model=schema.StorageAreaSchema, summary="사용자 공간 수정")
def update_user_storage_space(
    user_no: int, 
    area_no: int, 
    storage_data: schema.StorageAreaUpdate, 
    db: Session = Depends(get_db), 
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 현재 로그인한 사용자만 자신의 저장 공간을 수정할 수 있도록 제한
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to update this storage space.")
    
    space = crud.update_storage_space(db=db, user_no=user_no, area_no=area_no, area_name=storage_data.area_name)
    return space


# 사용자 공간 삭제
@router.delete("/{user_no}/spaces/{area_no}", summary="사용자 공간 삭제")
def delete_user_storage_space(
    user_no: int, 
    area_no: int, 
    db: Session = Depends(get_db), 
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 현재 로그인한 사용자만 자신의 저장 공간을 삭제할 수 있도록 제한
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this storage space.")
    
    # 공간에 방이 존재하는지 확인
    rooms = crud.get_rooms_by_area(db=db, area_no=area_no)
    if rooms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete storage area because rooms are associated with it. Please remove rooms first."
        )
    
    return crud.delete_storage_space(db=db, user_no=user_no, area_no=area_no)

# 방 추가
@router.post("/room", response_model=schema.RoomSchema, summary="방 추가")
def create_room(
    room: schema.RoomCreate,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 사용자가 소유한 공간에 방을 추가할 수 있는지 확인
    user_areas = crud.get_areas_by_user(db, user_no=current_user.user_no)
    if room.area_no not in [area.area_no for area in user_areas]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to add a room to this area."
        )

    # 방 생성
    new_room = crud.create_room(
        db=db,
        area_no=room.area_no,
        room_name=room.room_name
    )

    # 방 전체 정보를 반환 (room_no 포함)
    return new_room

# 방 조회
@router.get("/room/{room_no}", response_model=schema.RoomSchema, summary="방 조회")
def read_room(
    room_no: int,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    room = crud.get_room(db=db, room_no=room_no)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # 방이 현재 사용자의 소유 공간에 있는지 확인
    user_areas = crud.get_areas_by_user(db, user_no=current_user.user_no)
    if room.area_no not in [area.area_no for area in user_areas]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this room.")

    return room

# 특정 공간의 모든 방 조회
@router.get("/room/{area_no}/rooms", response_model=List[schema.RoomSchema], summary="특정 공간의 모든 방 조회")
def read_rooms_by_area(
    area_no: int,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 사용자가 소유한 공간인지 확인
    user_areas = crud.get_areas_by_user(db, user_no=current_user.user_no)
    if area_no not in [area.area_no for area in user_areas]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access rooms in this area.")

    rooms = crud.get_rooms_by_area(db=db, area_no=area_no)

    return rooms if rooms else []

# 방 수정
@router.put("/room/{room_no}", response_model=schema.RoomSchema, summary="방 수정")
def update_room(
    room_no: int,
    room_data: schema.RoomUpdate,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    room = crud.get_room(db=db, room_no=room_no)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # 방이 현재 사용자의 소유 공간에 있는지 확인
    user_areas = crud.get_areas_by_user(db, user_no=current_user.user_no)
    if room.area_no not in [area.area_no for area in user_areas]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this room.")

    updated_room = crud.update_room(db=db, room_no=room_no, room_data=room_data)
    return updated_room

# 방 삭제
@router.delete("/room/{room_no}", summary="방 삭제")
def delete_room(
    room_no: int,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    room = crud.get_room(db=db, room_no=room_no)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # 방이 현재 사용자의 소유 공간에 있는지 확인
    user_areas = crud.get_areas_by_user(db, user_no=current_user.user_no)
    if room.area_no not in [area.area_no for area in user_areas]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this room.")

    # 방에 가구가 존재하는지 확인
    storages = crud.get_storages_by_room(db=db, room_no=room_no)
    if storages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete room because furniture is associated with it. Please remove furniture first."
        )

    return crud.delete_room(db=db, room_no=room_no)

# 가구 추가
@router.post("/storage/", response_model=schema.Storage, summary="가구 추가")
def create_storage(
    storage: schema.StorageCreate,
    db: Session = Depends(get_db), 
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 해당 방이 현재 사용자 소유의 공간에 있는지 확인
    user_rooms = crud.get_rooms_by_user(db, user_no=current_user.user_no)  # 사용자가 소유한 모든 방 조회
    if storage.room_no not in [room.room_no for room in user_rooms]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add furniture to this room."
        )

    db_storage = crud.create_storage(db=db, storage=storage)
    return db_storage
    
# 가구 조회
@router.get("/storage/{storage_no}", response_model=schema.Storage, summary="가구 조회")
def read_storage(
    storage_no: int, 
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 가구가 존재하는지 확인
    db_storage = crud.get_storage(db, storage_no=storage_no)
    if not db_storage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    # 가구가 현재 사용자의 소유 방에 있는지 확인
    user_rooms = crud.get_rooms_by_user(db, user_no=current_user.user_no)  # 사용자가 소유한 모든 방 조회
    if db_storage.room_no not in [room.room_no for room in user_rooms]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this furniture.")

    return db_storage

# 특정 방에 있는 모든 가구 조회
@router.get("/storage/{room_no}/storages", response_model=List[schema.Storage], summary="특정 방에 있는 모든 가구 조회")
def get_storages_by_room(
    room_no: int, 
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 특정 방에 있는 모든 가구 조회
    storages = crud.get_storages_by_room(db, room_no)

    # 해당 방이 현재 사용자 소유의 공간에 있는지 확인
    user_rooms = crud.get_rooms_by_user(db, user_no=current_user.user_no)  # 사용자가 소유한 모든 방 조회
    if room_no not in [room.room_no for room in user_rooms]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this room.")

    return storages if storages else []

# 가구 수정
@router.put("/storage/{storage_no}", response_model=schema.Storage, summary="가구 수정")
def update_storage(
    storage_no: int,
    storage: schema.StorageUpdate, 
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 가구가 존재하는지 확인
    db_storage = crud.get_storage(db, storage_no=storage_no)
    if not db_storage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    # 가구가 현재 사용자가 소유한 방에 있는지 확인
    if db_storage.room_no not in [room.room_no for room in crud.get_rooms_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this furniture.")
    
    # 가구 수정 로직 호출
    updated_storage = crud.update_storage(db=db, storage_no=storage_no, storage_data=storage)
    return updated_storage


# 가구 삭제
@router.delete("/storage/{storage_no}", summary="가구 삭제")
def  delete_storage(
    storage_no: int, 
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 가구가 존재하는지 확인
    db_storage = crud.get_storage(db, storage_no=storage_no)
    if not db_storage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    # 가구에 물건이 존재하는지 확인
    items = crud.get_items_by_storage(db=db, storage_no=storage_no)
    if items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete storage because items are associated with it. Please remove items first."
        )

    return crud.delete_storage(db=db, storage_no=storage_no)


# 물건 추가
@router.post("/item", summary="물건 추가")
async def create_item_route(
    storage_no: int = Form(...),
    item_name: str = Form(...),
    item_type: str = Form(...),
    item_quantity: int = Form(...),
    row_num: Optional[int] = Form(None),
    item_Expiration_date: Optional[date] = Form(None),
    file: Optional[UploadFile] = File(None),  # 이미지 파일은 선택 사항
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 해당 가구가 현재 사용자 소유인지 확인
    storage = crud.get_storage(db=db, storage_no=storage_no)
    if storage.room_no not in [room.room_no for room in crud.get_rooms_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=403, detail="You do not have permission to add items to this storage.")

     # ItemCreate 스키마 생성
    item_data = schema.ItemCreate(
        storage_no=storage_no,
        item_name=item_name,
        row_num=row_num,
        item_type=item_type,
        item_quantity=item_quantity,
        item_Expiration_date=item_Expiration_date
    )

    # 물건 추가
    new_item = crud.create_item(db=db, item=item_data, file=file)
    return {"msg": "Item created successfully", "item_id": new_item.item_id}

# 물건 조회
@router.get("/item/{item_id}", response_model=schema.ItemCreate, summary="물건 조회")
def read_item(item_id: int, db: Session = Depends(get_db), current_user: schema.User = Depends(auth.get_current_user)):
    # 물건이 존재하는지 확인
    db_item = crud.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # 물건이 현재 사용자의 소유 가구에 있는지 확인
    storage = crud.get_storage(db=db, storage_no=db_item.storage_no)
    if storage.room_no not in [room.room_no for room in crud.get_rooms_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this item.")

    return db_item

# 물건 이미지 조회
@router.get("/item-image/{item_id}", summary="물건 이미지 조회")
def get_item_image(item_id: int, db: Session = Depends(get_db)):
    image_path = crud.get_item_image_url(db=db, item_id=item_id)

    # 이미지 파일이 실제로 존재하는지 확인
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # 파일 확장자에 따라 media_type 설정
    file_extension = os.path.splitext(image_path)[1].lower()
    media_type = "image/jpeg" if file_extension in [".jpg", ".jpeg"] else "image/png"

    return Response(content=image_data, media_type=media_type)

# 특정 가구에 있는 모든 물건 조회
@router.get("/storage/{storage_no}/items", response_model=List[schema.ItemSchema], summary="특정 가구에 있는 모든 물건 조회")
def get_items_by_storage_route(
    storage_no: int,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 현재 사용자가 소유한 가구인지 확인
    storage = crud.get_storage(db=db, storage_no=storage_no)
    if not storage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    # 가구가 현재 사용자의 소유 공간에 있는지 확인
    user_rooms = crud.get_rooms_by_user(db, user_no=current_user.user_no)
    if storage.room_no not in [room.room_no for room in user_rooms]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access items in this storage.")
    
    # 특정 가구에 있는 모든 물건 조회
    items = crud.get_items_by_storage(db=db, storage_no=storage_no)
    return items if items else []

# 물건 수정
@router.put("/item/{item_id}", response_model=schema.ItemCreate, summary="물건 수정")
async def update_item_route(
    item_id: int,
    item: schema.ItemUpdate,
    file: Optional[UploadFile] = File(None),  # 이미지 파일은 선택 사항
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 물건이 존재하는지 확인
    db_item = crud.get_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # 물건이 현재 사용자의 소유 가구에 있는지 확인
    storage = crud.get_storage(db=db, storage_no=db_item.storage_no)
    if storage.room_no not in [room.room_no for room in crud.get_rooms_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this item.")

    updated_item = crud.update_item(db=db, item_id=item_id, item_data=item, file=file)
    return updated_item


# 물건 삭제
@router.delete("/item/{item_id}", summary="물건 삭제")
def delete_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 물건이 존재하는지 확인
    db_item = crud.get_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # 물건이 현재 사용자의 소유 가구에 있는지 확인
    storage = crud.get_storage(db=db, storage_no=db_item.storage_no)
    if storage.room_no not in [room.room_no for room in crud.get_rooms_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this item.")

    return crud.delete_item(db=db, item_id=item_id)

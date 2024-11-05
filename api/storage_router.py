from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import app.crud as crud
import app.schema as schema
import app.auth  as auth
from app.database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from sqlalchemy.exc import IntegrityError

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

    # Pydantic 모델로 변환
    return [schema.StorageAreaSchema.model_validate(space) for space in spaces]


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
    
    return crud.delete_storage_space(db=db, user_no=user_no, area_no=area_no)

# 방 추가
@router.post("/room", response_model=schema.RoomCreate, summary="방 추가")
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
    return crud.create_room(
        db=db,
        area_no=room.area_no,
        room_name=room.room_name
    )

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
@router.get("/area/{area_no}/rooms", response_model=List[schema.RoomSchema], summary="특정 공간의 모든 방 조회")
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
    if not rooms:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No rooms found for this area")

    return rooms

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

    try:
        # 방 삭제 시도
        return crud.delete_room(db=db, room_no=room_no)

    except IntegrityError:
        # 무결성 제약 조건 위반 시 에러 메시지 반환
        db.rollback()  # 트랜잭션 롤백
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete room because items are associated with it. Please remove items first."
        )

# 가구 추가
@router.post("/storage/", response_model=schema.Storage, summary="가구 추가")
def create_storage(
    storage: schema.StorageCreate,
    db: Session = Depends(get_db), 
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 해당 공간이 현재 사용자 소유인지 확인
    user_areas = crud.get_areas_by_user(db, user_no=current_user.user_no)
    if storage.area_no not in [area.area_no for area in user_areas]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add furniture to this area."
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

    # 가구가 현재 사용자의 소유 공간에 있는지 확인
    if db_storage.area_no not in [area.area_no for area in crud.get_areas_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this furniture.")
    
    return db_storage

# 특정 공간에 있는 모든 가구 조회
@router.get("/storage/{area_no}/storages", response_model=List[schema.Storage], summary="특정 공간에 있는 모든 가구 조회")
def get_storages_by_area(
    area_no: int, 
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 특정 공간에 있는 모든 가구 조회
    storages = crud.get_storages_by_area(db=db, area_no=area_no)

    if not storages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No storage found for this area.")

    # 해당 공간이 현재 사용자 소유인지 확인
    user_areas = crud.get_areas_by_user(db, user_no=current_user.user_no)
    if area_no not in [area.area_no for area in user_areas]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this area.")

    return storages

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

    # 가구가 현재 사용자의 소유 공간에 있는지 확인
    if db_storage.area_no not in [area.area_no for area in crud.get_areas_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this furniture.")
    
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

    # 가구가 현재 사용자의 소유 공간에 있는지 확인
    if db_storage.area_no not in [area.area_no for area in crud.get_areas_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this furniture.")

    db_storage = crud.delete_storage(db=db, storage_no=storage_no)
    return db_storage

# 물건 추가
@router.post("/item", response_model=schema.ItemCreate, summary="물건 추가")
def create_item(item: schema.ItemCreate, db: Session = Depends(get_db), current_user: schema.User = Depends(auth.get_current_user)):
    # 해당 상세 저장 위치가 현재 사용자 소유인지 확인
    detail_storage = crud.get_detail_storage(db=db, detail_storage_no=item.detail_storage_no)
    if detail_storage.area_no not in [area.area_no for area in crud.get_areas_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to add items to this detail storage.")
    
    return crud.create_item(db=db, item=item)

# 물건 수정
@router.put("/item/{item_id}", response_model=schema.ItemCreate, summary="물건 수정")
def update_item(
    item_id: int,
    item: schema.ItemUpdate,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 물건이 존재하는지 확인
    db_item = crud.get_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # 물건이 현재 사용자의 소유 공간에 있는지 확인
    if db_item.detail_storage_no not in [
        detail_storage.detail_storage_no 
        for detail_storage in crud.get_all_detail_storages_by_user(db, user_no=current_user.user_no)    
    ]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this item.")

    updated_item = crud.update_item(db=db, item_id=item_id, item_data=item)
    return updated_item

# 물건 조회
@router.get("/item/{item_id}", response_model=schema.ItemCreate, summary="물건 조회")
def read_item(item_id: int, db: Session = Depends(get_db), current_user: schema.User = Depends(auth.get_current_user)):
    item = crud.get_item(db=db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # 해당 물건이 현재 사용자의 소유 공간에 있는지 확인
    detail_storage = crud.get_detail_storage(db=db, detail_storage_no=item.detail_storage_no)
    if detail_storage.area_no not in [area.area_no for area in crud.get_areas_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this item.")
    
    return item

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

    # 물건이 현재 사용자의 소유 공간에 있는지 확인
    if db_item.detail_storage.area_no not in [area.area_no for area in crud.get_areas_by_user(db, user_no=current_user.user_no)]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this item.")

    return crud.delete_item(db=db, item_id=item_id)

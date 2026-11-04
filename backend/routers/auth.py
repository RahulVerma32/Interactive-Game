from fastapi import APIRouter, Depends
from core.auth import current_user

router = APIRouter(prefix='/auth', tags=['auth'])


@router.get('/me')
def get_current_user(user_id: str = Depends(current_user)):
    return {'user_id': user_id.removeprefix('user:')}

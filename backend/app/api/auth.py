"""认证API路由"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta

from app.config import settings
from app.schemas import LoginRequest, Token, User, Message

router = APIRouter()
security = HTTPBearer(auto_error=False)


def create_access_token(username: str) -> str:
    """创建JWT token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前用户（require_login=false 时无需认证）"""
    if not settings.REQUIRE_LOGIN:
        return User(username="anonymous")

    if credentials is None:
        raise HTTPException(status_code=401, detail="未提供认证凭据")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
        return User(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证凭据")


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """用户登录"""
    if not settings.REQUIRE_LOGIN:
        access_token = create_access_token("admin")
        return Token(access_token=access_token)

    if settings.USERS.get(request.username) != request.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token(request.username)
    return Token(access_token=access_token)


@router.post("/logout", response_model=Message)
async def logout(user: User = Depends(get_current_user)):
    """用户登出（前端清除token即可）"""
    return Message(message=f"用户 {user.username} 已登出")


@router.get("/me", response_model=User)
async def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return user


@router.get("/check")
async def check_auth():
    """检查是否需要登录（无需认证）"""
    return {"require_login": settings.REQUIRE_LOGIN}

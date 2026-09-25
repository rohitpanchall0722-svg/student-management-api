from sqlalchemy.orm import Session
from backend.app.models.users import RefreshToken
from sqlalchemy import select
class RefreshTokenRepositiory:

    def create(self,db:Session,
                                 token:str,
                             expire_at,
                             user_id=None,
                             admin_id=None):
        refresh_token = RefreshToken(
            user_id=user_id,
                admin_id=admin_id,
            token=token,
            expire_at=expire_at
        )
        db.add(refresh_token)
        db.flush()
        db.refresh(refresh_token)

        return refresh_token

    def get_by_token(self,db:Session,token:str):
        stmt = select(RefreshToken).where(RefreshToken.token==token)
        result = db.execute(stmt).scalar_one_or_none()
        return result

    def revoke_token(self,db:Session,refresh_token:RefreshToken):
        refresh_token.revoked_at=True
        db.flush()
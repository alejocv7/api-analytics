import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core import db, security
from app.core.config import settings
from app.core.enums import ProjectRole
from app.services import project_service, user_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_initial_data(session: AsyncSession) -> None:
    """
    Idempotent: safe to run on every startup.

    It creates:
    - A system user for the application's own analytics (if PROJECT_ID > 0)
    - A self-monitoring project linked to the system user and PROJECT_ID
    """

    if not settings.PROJECT_KEY:
        logger.error("PROJECT_KEY is not set. Skipping seeding.")
        return

    # Use a system email
    system_email = settings.PROJECT_USER
    user = await user_service.get_user_by_email(system_email, session)
    if not user:
        logger.info("Creating system user for self-monitoring...")
        hashed_password = security.hash_password(settings.PROJECT_PASSWORD)
        user = models.User(
            email=system_email,
            hashed_password=hashed_password,
            full_name="System Monitor",
            is_active=True,
        )
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
            logger.info("System user created (id: %s)", user.id)
        except Exception:
            await session.rollback()
            # If it failed, maybe it was created by another worker
            user = await user_service.get_user_by_email(system_email, session)
            if not user:
                raise

    # 2. Check if the self-monitoring project exists
    project = await project_service.get_user_project_by_key(
        user.id, settings.PROJECT_KEY, session
    )
    if not project:
        logger.info(
            "Creating self-monitoring project (key: %s)...", settings.PROJECT_KEY
        )

        project = models.Project(
            name=f"{settings.PROJECT_NAME} Self-Monitoring",
            description=settings.PROJECT_DESCRIPTION,
            project_key=settings.PROJECT_KEY,
            user_id=user.id,
            is_active=True,
        )
        session.add(project)
        try:
            await session.flush()  # get project.id without committing
            owner_membership = models.UserProject(
                user_id=user.id, project_id=project.id, role=ProjectRole.owner
            )
            session.add(owner_membership)
            await session.commit()
            logger.info("Self-monitoring project created (id: %s)", project.id)
        except Exception:
            await session.rollback()
            # If it failed, maybe it was created by another worker
            project = await project_service.get_user_project_by_key(
                user.id, settings.PROJECT_KEY, session
            )
            if not project:
                raise


async def main() -> None:
    logger.info("Starting seed data process...")
    async with db.AsyncSessionLocal() as session:
        await seed_initial_data(session)
    logger.info("Seed data process completed.")


if __name__ == "__main__":
    asyncio.run(main())

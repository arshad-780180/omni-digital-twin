import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING

logger = logging.getLogger("omni.database")

CORE_COLLECTIONS = [
    "users",
    "profiles",
    "resumes",
    "github_analysis",
    "career_analysis",
    "ats_analysis",
    "job_matches",
    "digital_twin_memory",
    "interview_sessions",
    "learning_roadmaps",
]


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Creates standard indexes across all core OMNI Digital Twin collections:
    - user_id
    - created_at
    - (user_id, created_at)
    Avoids duplicate index creation and logs index setup.
    """
    try:
        # Standard index models for user_id and created_at queries
        standard_indexes = [
            IndexModel([("user_id", ASCENDING)], name="idx_user_id"),
            IndexModel([("created_at", DESCENDING)], name="idx_created_at"),
            IndexModel(
                [("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_user_id_created_at",
            ),
        ]

        for collection_name in CORE_COLLECTIONS:
            coll = db[collection_name]
            # Create indexes without failing if they already exist
            await coll.create_indexes(standard_indexes)

        # Unique email index on users table
        await db.users.create_index([("email", ASCENDING)], unique=True, name="idx_users_email")

        logger.info("[Database] Core MongoDB indexes verified successfully.")
    except Exception as e:
        logger.warning(f"[Database] Notice while creating MongoDB indexes: {str(e)}")

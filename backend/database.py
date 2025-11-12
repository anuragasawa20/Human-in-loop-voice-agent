"""
Firebase Firestore database client and utilities.

Design Decision:
- Firebase Firestore for real-time updates
- Service layer abstraction for easy database swapping if needed
- Connection pooling and error handling
"""

import logging
import os
from typing import Optional
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
from dotenv import load_dotenv

load_dotenv(".env.local")

logger = logging.getLogger(__name__)


class FirebaseClient:
    """
    Firebase Firestore client wrapper.

    Design Decision:
    - Singleton pattern to reuse connection
    - Automatic initialization
    - Error handling with fallbacks
    """

    _instance: Optional["FirebaseClient"] = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._db is None:
            self._initialize()

    def _initialize(self):
        """Initialize Firebase connection."""
        try:
            credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            project_id = os.getenv("FIREBASE_PROJECT_ID")

            if credentials_path and os.path.exists(credentials_path):
                # Use service account credentials
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(
                    cred,
                    {
                        "projectId": project_id,
                    },
                )
                logger.info(
                    f"Firebase initialized with credentials: {credentials_path}"
                )
            else:
                # Use default credentials (for Cloud Run, local development)
                logger.warning(
                    "FIREBASE_CREDENTIALS_PATH not set - Firebase features disabled"
                )
                logger.info(
                    "Voice demo will work, but help requests/knowledge base won't"
                )
                # Don't initialize Firebase - allow backend to run without it
                self._db = None
                return

            self._db = firestore.client()
            logger.info("Firestore client connected")

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            logger.warning("Firebase disabled - Voice demo will still work")
            self._db = None  # Don't crash, just disable Firebase features

    @property
    def db(self):
        """Get Firestore database client."""
        if self._db is None:
            self._initialize()
        if self._db is None:
            raise RuntimeError(
                "Firebase not initialized. "
                "Set FIREBASE_CREDENTIALS_PATH to enable database features."
            )
        return self._db

    def collection(self, name: str):
        """Get a collection reference."""
        if self._db is None:
            raise RuntimeError(
                "Firebase not initialized. "
                "Database features are disabled."
            )
        return self.db.collection(name)
    
    def is_connected(self) -> bool:
        """Check if Firebase is connected."""
        return self._db is not None

    def close(self):
        """Close Firebase connection."""
        try:
            firebase_admin.delete_app(firebase_admin.get_app())
            self._db = None
            logger.info("Firebase connection closed")
        except Exception as e:
            logger.warning(f"Error closing Firebase: {e}")


# Global database client instance
db_client = FirebaseClient()


def get_db():
    """
    Dependency injection for FastAPI.

    Returns:
        FirebaseClient instance
    """
    return db_client

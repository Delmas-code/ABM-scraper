from pymongo import MongoClient
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import time
import logging

class MongoDataHandler:
    def __init__(self, 
                connection_string: str,
                database_name: str,
                collection_name: str,
                buffer_size: int = 100,
                max_wait_time: int = 60):
        """
        Initialize the data inserter.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection
            buffer_size: Number of documents to buffer before inserting
            max_wait_time: Maximum time (in seconds) to wait before forcing an insert
        """

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('MongoDataHandler')


        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection_name = collection_name
        self.buffer_size = buffer_size
        self.max_wait_time = max_wait_time
        
        # Create buffer for documents
        self.buffer: List[Dict[str, Any]] = []
        self.last_insert_time = time.time()
        
        # Ensure collection exists
        if collection_name not in self.db.list_collection_names():
            self.db.create_collection(collection_name)
        
        self.collection = self.db[collection_name]
        
        self.logger.info(f"Connected to DB: {self.db} and Collection: {self.collection_name} ")
    
    def add_document(self, document: Dict[str, Any]) -> None:
        """
        Add a document to the buffer and insert if conditions are met.
        
        Args:
            document: Dictionary containing the document data
        """
        self.buffer.append(document)
        
        # Check if we should insert based on buffer size or time
        if (len(self.buffer) >= self.buffer_size or 
            time.time() - self.last_insert_time >= self.max_wait_time):
            self.flush_buffer()
    
    def flush_buffer(self) -> None:
        """Force insert all documents currently in the buffer."""
        if not self.buffer:
            return
            
        try:
            self.collection.insert_many(self.buffer)
            print(f"Inserted {len(self.buffer)} documents")
        except Exception as e:
            self.logger.error(f"Error inserting documents: {str(e)}")
        
        self.buffer = []
        self.last_insert_time = time.time()
    
    def __del__(self):
        """Ensure remaining documents are inserted when object is destroyed."""
        self.flush_buffer()
        self.client.close()
        self.logger.info(f"Connection to database {self.db} has been closed! ")

    def insert_document(self, document) -> Optional[str]:
        """
            Insert a single document into MongoDB Atlas and return its ID.
        """
        try:
            
            # Insert the document
            result = self.collection.insert_one(document)
            
            # Get the inserted document's ID
            document_id = str(result.inserted_id)
            print(f"Document inserted successfully with ID: {document_id}")
            return document_id
            
        except Exception as e:
            self.logger.error(f"Error inserting documents: {str(e)}")
            return None
            
        finally:
            # Close the connection
            self.client.close()

    def check_and_create_document(self, name: str) -> Optional[str]:

        try:
            
            # Check if document with this name exists
            existing_doc = self.collection.find_one({"name": name})
            
            if existing_doc:
                # Document exists, return its ID
                return str(existing_doc['_id'])
            else:
                # Document doesn't exist, create new one
                # Add name and timestamp to the document data
                document_data = {
                    "name": name,
                    "created_at": datetime.now(timezone.utc)
                }
                
                # Insert the document
                result = self.collection.insert_one(document_data)
                return str(result.inserted_id)
                
        except Exception as e:
            self.logger.error(f"Error in check_and_create_document: {str(e)}")
            return None
            
        finally:
            # Close the connection
            self.client.close()

# services.py
import os
import hashlib
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from web.models.chatbot import Chatbot
from web.models.pdf_data_sources import PdfDataSource, PdfDataSourceErrorLog
from uuid import uuid4
import secrets

class HandlePdfDataSource:
    def __init__(self, bot: Chatbot, files):
        self.bot = bot
        self.files = files

    def handle(self) -> PdfDataSource:
        data_source = PdfDataSource()
        data_source.bot = self.bot

        folder_name = secrets.token_hex(20)
        folder_path = f"website_data_sources/{folder_name}"

        files_urls = []
        files_info_list = []
        for file in self.files:
            try:
                # Validate file types or other conditions if necessary
                # For example: if not file.name.endswith('.pdf'): raise ValidationError('Invalid file type')

                # Generate a unique file name using UUID
                file_extension = os.path.splitext(file.name)[1]
                file_uuid_name = str(uuid4()) + file_extension
                file_path = os.path.join(folder_path, file_uuid_name)

                # Generate hash of the file content
                file_hash = hashlib.md5(file.read()).hexdigest()
                file.seek(0)  # Reset file pointer to beginning
                
                # Create the directory if it does not exist
                directory = os.path.dirname(file_path)
                os.makedirs(directory, exist_ok=True)

                # Check if the directory was created successfully
                if not os.path.isdir(directory):
                    raise Exception(f"Failed to create directory: {directory}")

                # Save the file to the storage system
                default_storage.save(file_path, file)

                # Save file info
                files_info = {
                    'original_name': file.name,
                    'uuid_name': file_uuid_name,
                    'hash': file_hash
                }
                files_urls.append(file_path)
                files_info_list.append(files_info)

            except Exception as e:
                # Log the exception for debugging purposes
                print(f"Error while uploading file: {file.name}, Error: {str(e)}")
                # You can log the exception to a file or use a proper logging framework
                error_log = PdfDataSourceErrorLog(pdf_data_source=data_source, error_message=str(e))
                error_log.save()
                # You can also raise a more specific custom exception if needed
                raise ValidationError(f"Error while uploading file: {file.name}, Error: {str(e)}")
        
        data_source.chatbot_id = self.bot.id
        data_source.files = files_urls
        data_source.files_info = files_info_list
        data_source.folder_name = folder_name
        data_source.ingest_status = 'PDF(s) Uploaded'

        data_source.save()
        return data_source

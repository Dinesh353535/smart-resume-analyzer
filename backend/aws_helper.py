import boto3
import os
from datetime import datetime

def upload_to_s3(file_path, filename):
    """Upload resume PDF to AWS S3 bucket"""
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )

        bucket_name = os.environ.get("AWS_BUCKET_NAME")

        # Create unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"resumes/{timestamp}_{filename}"

        s3.upload_file(
            file_path,
            bucket_name,
            s3_key,
            ExtraArgs={"ContentType": "application/pdf"}
        )

        # Generate public URL
        url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        return {"success": True, "url": url, "key": s3_key}

    except Exception as e:
        return {"success": False, "error": str(e)}


def list_uploaded_resumes():
    """List all resumes stored in S3"""
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )

        bucket_name = os.environ.get("AWS_BUCKET_NAME")
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix="resumes/")

        files = []
        if "Contents" in response:
            for obj in response["Contents"]:
                files.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "uploaded_at": obj["LastModified"].strftime("%Y-%m-%d %H:%M")
                })

        return {"success": True, "files": files}

    except Exception as e:
        return {"success": False, "error": str(e)}
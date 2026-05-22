# from fastapi import (
#     APIRouter, Depends, HTTPException,
#     UploadFile, File, BackgroundTasks, Request
# )
# from sqlalchemy.orm import Session
# from typing import List
# from .. import models, schemas
# from ..database import get_db
# from ..auth import get_current_user, require_admin
# from ..services import storage, mpesa, ai_service
# from services.email_tasks import send_notification_email
# from services.sms_tasks import send_payment_confirmation_sms
# from ..services.notification_tasks import create_notification
# import json


# # ══════════════════════════════════════════════════════════
# # PAYMENTS ROUTER
# # ══════════════════════════════════════════════════════════

# payments_router = APIRouter(prefix="/api/payments", tags=["Payments"])


# @payments_router.post("/mpesa/initiate", response_model=schemas.MessageResponse)
# async def initiate_mpesa_payment(
#     payment_data: schemas.MpesaPaymentRequest,
#     db:           Session     = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     """Initiate M-Pesa STK push payment"""
#     result = await mpesa.initiate_stk_push(
#         phone       = payment_data.phone,
#         amount      = payment_data.amount,
#         description = payment_data.description
#     )

#     # create pending payment record
#     payment = models.Payment(
#         user_id        = current_user.id,
#         amount         = payment_data.amount,
#         currency       = "KES",
#         status         = "pending",
#         payment_method = "mpesa",
#         phone_number   = payment_data.phone,
#         description    = payment_data.description,
#         metadata       = json.dumps(result)
#     )
#     db.add(payment)
#     db.commit()

#     return {
#         "message": "Payment initiated. Check your phone for M-Pesa prompt.",
#         "success": True,
#         "data":    result
#     }


# @payments_router.post("/mpesa/callback")
# async def mpesa_callback(
#     callback_data: dict,
#     db:            Session = Depends(get_db)
# ):
#     """
#     M-Pesa callback — called by Safaricom servers
#     This URL must be publicly accessible
#     """
#     result = mpesa.process_mpesa_callback(callback_data)

#     if result["success"]:
#         # update payment record
#         transaction_id = result.get("transaction_id")
#         payment = db.query(models.Payment).filter(
#             models.Payment.transaction_id == None,
#             models.Payment.status == "pending"
#         ).first()

#         if payment:
#             payment.status         = "completed"
#             payment.transaction_id = transaction_id
#             db.commit()

#             # notify user via SMS in background
#             send_payment_confirmation_sms.delay(
#                 result.get("phone"),
#                 result.get("amount"),
#                 transaction_id
#             )

#             # create in-app notification
#             create_notification.delay(
#                 user_id = payment.user_id,
#                 title   = "Payment Confirmed",
#                 message = f"Your payment of KES {result.get('amount')} was received.",
#                 type    = "success"
#             )

#     return {"ResultCode": 0, "ResultDesc": "Success"}


# @payments_router.get("/history", response_model=List[schemas.PaymentResponse])
# def payment_history(
#     db:           Session     = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     return db.query(models.Payment).filter(
#         models.Payment.user_id == current_user.id
#     ).order_by(models.Payment.created_at.desc()).all()


# # ══════════════════════════════════════════════════════════
# # FILES ROUTER
# # ══════════════════════════════════════════════════════════

# files_router = APIRouter(prefix="/api/files", tags=["Files"])


# @files_router.post("/upload", response_model=schemas.FileResponse)
# async def upload_file(
#     file:         UploadFile  = File(...),
#     db:           Session     = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     """Upload any file to S3"""
#     result = await storage.upload_file_to_s3(file=file, folder="uploads")

#     file_record = models.FileUpload(
#         user_id       = current_user.id,
#         filename      = result["filename"],
#         original_name = result["original_name"],
#         file_size     = result["file_size"],
#         content_type  = result["content_type"],
#         s3_key        = result["s3_key"],
#         url           = result["url"]
#     )
#     db.add(file_record)
#     db.commit()
#     db.refresh(file_record)
#     return file_record


# @files_router.get("/", response_model=List[schemas.FileResponse])
# def list_my_files(
#     db:           Session     = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     return db.query(models.FileUpload).filter(
#         models.FileUpload.user_id == current_user.id
#     ).all()


# @files_router.delete("/{file_id}", response_model=schemas.MessageResponse)
# def delete_file(
#     file_id:      int,
#     db:           Session     = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     file = db.query(models.FileUpload).filter(
#         models.FileUpload.id      == file_id,
#         models.FileUpload.user_id == current_user.id
#     ).first()

#     if not file:
#         raise HTTPException(status_code=404, detail="File not found")

#     storage.delete_file_from_s3(file.s3_key)
#     db.delete(file)
#     db.commit()
#     return {"message": "File deleted", "success": True}


# # ══════════════════════════════════════════════════════════
# # NOTIFICATIONS ROUTER
# # ══════════════════════════════════════════════════════════

# notifications_router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# @notifications_router.get("/", response_model=List[schemas.NotificationResponse])
# def get_notifications(
#     unread_only:  bool        = False,
#     db:           Session     = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     query = db.query(models.Notification).filter(
#         models.Notification.user_id == current_user.id
#     )
#     if unread_only:
#         query = query.filter(models.Notification.is_read == False)

#     return query.order_by(models.Notification.created_at.desc()).limit(50).all()


# @notifications_router.patch("/{notification_id}/read")
# def mark_as_read(
#     notification_id: int,
#     db:              Session     = Depends(get_db),
#     current_user:    models.User = Depends(get_current_user)
# ):
#     notification = db.query(models.Notification).filter(
#         models.Notification.id      == notification_id,
#         models.Notification.user_id == current_user.id
#     ).first()

#     if not notification:
#         raise HTTPException(status_code=404, detail="Notification not found")

#     notification.is_read = True
#     db.commit()
#     return {"message": "Marked as read", "success": True}


# @notifications_router.patch("/read-all")
# def mark_all_read(
#     db:           Session     = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     db.query(models.Notification).filter(
#         models.Notification.user_id == current_user.id,
#         models.Notification.is_read == False
#     ).update({"is_read": True})
#     db.commit()
#     return {"message": "All notifications marked as read", "success": True}


# # ══════════════════════════════════════════════════════════
# # AI ROUTER
# # ══════════════════════════════════════════════════════════

# ai_router = APIRouter(prefix="/api/ai", tags=["AI"])


# @ai_router.post("/chat", response_model=schemas.AIResponse)
# async def ai_chat(
#     request:      schemas.AIRequest,
#     current_user: models.User = Depends(get_current_user)
# ):
#     """Chat with AI — powered by OpenAI"""
#     return await ai_service.get_ai_response(request)


# @ai_router.post("/analyze-document", response_model=schemas.MessageResponse)
# async def analyze_document(
#     question:     str,
#     file:         UploadFile  = File(...),
#     current_user: models.User = Depends(get_current_user)
# ):
#     """Upload a document and ask AI questions about it"""
#     content = await file.read()
#     text    = content.decode("utf-8", errors="ignore")

#     answer = await ai_service.analyze_document(text, question)
#     return {"message": answer, "success": True}

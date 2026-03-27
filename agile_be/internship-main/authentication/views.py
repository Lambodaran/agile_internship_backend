from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from .models import User
from rest_framework.permissions import IsAuthenticated

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)

            # Replace this:
            # return Response({"token": token.key}, status=status.HTTP_201_CREATED)

            # With this:
            return Response({
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,  # adjust field name if different
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role')  # expect role from frontend

        user = authenticate(username=username, password=password)
        if user:
            if user.role != role:
                return Response({"error": "Invalid credentials for this role."}, status=status.HTTP_403_FORBIDDEN)

            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "access": token.key,
                "role": user.role,
                "username":user.username,
            })

        return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            
            request.user.auth_token.delete()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except:
            return Response({"error": "Logout failed."}, status=status.HTTP_400_BAD_REQUEST)
        
import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .serializers import (
    UserSerializer,
    RequestPasswordResetSerializer,
    VerifyResetCodeSerializer,
    ResetPasswordSerializer
)
from .models import User, PasswordResetCode
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
User = get_user_model()


class RequestPasswordResetView(APIView):
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "No user found with this email."},
                    status=status.HTTP_404_NOT_FOUND
                )

            PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

            code = str(random.randint(100000, 999999))

            PasswordResetCode.objects.create(
                user=user,
                code=code
            )

            subject = "Skyro Internship Management System - Password Reset Code"

            text_content = (
                f"Hello {user.username},\n\n"
                f"Your password reset code is: {code}\n\n"
                f"This code will expire in 10 minutes.\n\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"Skyro Internship Management System"
            )

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Password Reset Code</title>
            </head>
            <body style="margin:0; padding:0; background-color:#eef4ff; font-family:Arial, Helvetica, sans-serif;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #312e81 100%); padding: 40px 16px;">
                <tr>
                  <td align="center">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 640px; background-color: rgba(255,255,255,0.96); border-radius: 24px; overflow: hidden; box-shadow: 0 20px 50px rgba(15,23,42,0.25);">
                      
                      <!-- Top Brand Bar -->
                      <tr>
                        <td style="padding: 18px 28px; background: linear-gradient(90deg, #2563eb, #06b6d4, #7c3aed); text-align: center;">
                          <div style="font-size: 14px; letter-spacing: 0.8px; color: #ffffff; font-weight: 700; text-transform: uppercase;">
                            Skyro Internship Management System
                          </div>
                        </td>
                      </tr>

                      <!-- Header -->
                      <tr>
                        <td style="padding: 36px 32px 18px 32px; text-align: center;">
                          <div style="display: inline-block; background: #eff6ff; color: #2563eb; font-size: 13px; font-weight: 700; padding: 8px 16px; border-radius: 999px; margin-bottom: 18px;">
                            Password Reset Request
                          </div>

                          <h1 style="margin: 0; font-size: 30px; line-height: 1.3; color: #0f172a; font-weight: 800;">
                            Verify Your Reset Code
                          </h1>

                          <p style="margin: 16px 0 0 0; font-size: 16px; line-height: 1.7; color: #475569;">
                            Hello <strong style="color:#0f172a;">{user.username}</strong>,<br>
                            We received a request to reset your password for your
                            <strong>Skyro Internship Management System</strong> account.
                          </p>
                        </td>
                      </tr>

                      <!-- Code Box -->
                      <tr>
                        <td style="padding: 8px 32px 8px 32px;">
                          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: linear-gradient(135deg, #eff6ff 0%, #ecfeff 100%); border: 1px solid #bfdbfe; border-radius: 20px;">
                            <tr>
                              <td style="padding: 28px; text-align: center;">
                                <div style="font-size: 14px; color: #475569; margin-bottom: 12px; font-weight: 600;">
                                  Your One-Time Verification Code
                                </div>
                                <div style="font-size: 36px; letter-spacing: 10px; font-weight: 800; color: #1d4ed8; margin-bottom: 10px;">
                                  {code}
                                </div>
                                <div style="font-size: 14px; color: #64748b;">
                                  This code will expire in <strong>10 minutes</strong>.
                                </div>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>

                      <!-- Message -->
                      <tr>
                        <td style="padding: 24px 32px 8px 32px;">
                          <p style="margin: 0; font-size: 15px; line-height: 1.8; color: #475569;">
                            Enter this code in the password reset screen to continue securely.
                            For your protection, do not share this code with anyone.
                          </p>
                        </td>
                      </tr>

                      <!-- Alert Box -->
                      <tr>
                        <td style="padding: 18px 32px 10px 32px;">
                          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #fff7ed; border: 1px solid #fdba74; border-radius: 16px;">
                            <tr>
                              <td style="padding: 16px 18px; font-size: 14px; line-height: 1.7; color: #9a3412;">
                                <strong>Security Note:</strong> If you did not request a password reset,
                                you can safely ignore this email. Your account will remain unchanged.
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>

                      <!-- Footer -->
                      <tr>
                        <td style="padding: 28px 32px 34px 32px; text-align: center;">
                          <p style="margin: 0 0 8px 0; font-size: 14px; color: #64748b;">
                            This is an automated message from
                          </p>
                          <p style="margin: 0; font-size: 15px; font-weight: 700; color: #0f172a;">
                            Skyro Internship Management System
                          </p>
                        </td>
                      </tr>
                    </table>

                    <p style="margin: 18px 0 0 0; font-size: 12px; color: rgba(255,255,255,0.75);">
                      © 2026 Skyro Internship Management System. All rights reserved.
                    </p>
                  </td>
                </tr>
              </table>
            </body>
            </html>
            """

            email_message = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send(fail_silently=False)

            return Response(
                {"message": "Reset code sent to your email."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyResetCodeView(APIView):
    def post(self, request):
        serializer = VerifyResetCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "Invalid email."},
                    status=status.HTTP_404_NOT_FOUND
                )

            reset_obj = PasswordResetCode.objects.filter(
                user=user,
                code=code,
                is_used=False
            ).order_by('-created_at').first()

            if not reset_obj:
                return Response(
                    {"error": "Invalid code."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if reset_obj.is_expired():
                return Response(
                    {"error": "Code expired."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {"message": "Code verified successfully."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "Invalid email."},
                    status=status.HTTP_404_NOT_FOUND
                )

            reset_obj = PasswordResetCode.objects.filter(
                user=user,
                code=code,
                is_used=False
            ).order_by('-created_at').first()

            if not reset_obj:
                return Response(
                    {"error": "Invalid code."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if reset_obj.is_expired():
                return Response(
                    {"error": "Code expired."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.save()

            reset_obj.is_used = True
            reset_obj.save()

            # Optional: delete old login token so user logs in again
            Token.objects.filter(user=user).delete()

            return Response(
                {"message": "Password reset successful."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
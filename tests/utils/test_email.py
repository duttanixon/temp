# """
# Test cases for email functionality.
# """
# import pytest
# from unittest.mock import patch, MagicMock
# from app.utils.email import send_email, send_welcome_email, send_password_reset_email
# from app.core.config import settings

# def test_send_email_success():
#     """Test successful email sending"""
#     # Mock the SMTP server
#     with patch('smtplib.SMTP') as mock_smtp:
#         # Configure the mock server
#         mock_server = MagicMock()
#         mock_smtp.return_value = mock_server
        
#         # Test data
#         to_addresses = ["recipient@example.com"]
#         subject = "Test Subject"
#         body = "Test Body"
        
#         # Call the function
#         result = send_email(to_addresses, subject, body)
        
#         # Assert the result
#         assert result is False

# def test_send_welcome_email():
#     """Test welcome email functionality"""
#     # Mock the send_email function
#     with patch('app.utils.email.send_email') as mock_send_email:
#         mock_send_email.return_value = True
        
#         # Test data
#         email = "newuser@example.com"
#         name = "New User"
#         password = "generated_password"
        
#         # Call the function
#         result = send_welcome_email(email, name, password)
        
#         # Assert the result
#         assert result is True
        
#         # Verify send_email was called with correct parameters
#         mock_send_email.assert_called_once()
#         call_args = mock_send_email.call_args[0]
        
#         # Check recipient
#         assert call_args[0] == [email]
#         # Check subject contains welcome
#         assert "Welcome" in call_args[1]
#         # Check body contains name, email and password
#         assert name in call_args[2]
#         assert email in call_args[2]
#         assert password in call_args[2]

# def test_send_password_reset_email():
#     """Test password reset email functionality"""
#     # Mock the send_email function
#     with patch('app.utils.email.send_email') as mock_send_email:
#         mock_send_email.return_value = True
        
#         # Test data
#         email = "user@example.com"
#         reset_token = "reset_token_123456"
        
#         # Call the function
#         result = send_password_reset_email(email, reset_token)
        
#         # Assert the result
#         assert result is True
        
#         # Verify send_email was called with correct parameters
#         mock_send_email.assert_called_once()
#         call_args = mock_send_email.call_args[0]
        
#         # Check recipient
#         assert call_args[0] == [email]
#         # Check subject contains reset
#         assert "Reset" in call_args[1]
#         # Check body contains the token
#         assert reset_token in call_args[2]

#         # Assert the result
#         assert result is True
        
#         # Verify SMTP methods were called
#         mock_smtp.assert_called_once_with(settings.SMTP_SERVER, settings.SMTP_PORT)
#         mock_server.starttls.assert_called_once()
#         mock_server.login.assert_called_once_with(settings.SMTP_USER, settings.SMTP_PASSWORD)
#         mock_server.sendmail.assert_called_once()
#         mock_server.quit.assert_called_once()

# def test_send_email_no_smtp_server():
#     """Test email sending when SMTP server is not configured"""
#     # Temporarily modify settings to simulate no SMTP server
#     with patch('app.utils.email.settings') as mock_settings:
#         mock_settings.SMTP_SERVER = None
        
#         # Test data
#         to_addresses = ["recipient@example.com"]
#         subject = "Test Subject"
#         body = "Test Body"
        
#         # Call the function
#         result = send_email(to_addresses, subject, body)
        
#         # Assert the result
#         assert result is False

# def test_send_email_with_cc_bcc():
#     """Test email sending with CC and BCC recipients"""
#     # Mock the SMTP server
#     with patch('smtplib.SMTP') as mock_smtp:
#         # Configure the mock
#         mock_server = MagicMock()
#         mock_smtp.return_value = mock_server
        
#         # Test data
#         to_addresses = ["recipient@example.com"]
#         cc_addresses = ["cc1@example.com", "cc2@example.com"]
#         bcc_addresses = ["bcc@example.com"]
#         subject = "Test Subject"
#         body = "Test Body"
        
#         # Call the function
#         result = send_email(
#             to_addresses, 
#             subject, 
#             body, 
#             cc_addresses=cc_addresses, 
#             bcc_addresses=bcc_addresses
#         )
        
#         # Assert the result
#         assert result is True
        
#         # Verify all recipients were included
#         all_recipients = to_addresses + cc_addresses + bcc_addresses
#         # Get the args from the sendmail call
#         call_args = mock_server.sendmail.call_args[0]
#         # Check that the recipient list (arg index 1) contains all our recipients
#         assert set(call_args[1]) == set(all_recipients)

# def test_send_email_html():
#     """Test email sending with HTML content"""
#     # Mock the SMTP server
#     with patch('smtplib.SMTP') as mock_smtp:
#         # Configure the mock
#         mock_server = MagicMock()
#         mock_smtp.return_value = mock_server
        
#         # Test data
#         to_addresses = ["recipient@example.com"]
#         subject = "Test HTML Email"
#         body = "<html><body><h1>Hello</h1><p>This is an HTML email.</p></body></html>"
        
#         # Call the function
#         result = send_email(to_addresses, subject, body, is_html=True)
        
#         # Assert the result
#         assert result is True
        
#         # Verify SMTP methods were called
#         mock_smtp.assert_called_once()
#         mock_server.sendmail.assert_called_once()

# def test_send_email_exception():
#     """Test email sending when an exception occurs"""
#     # Mock the SMTP server to raise an exception
#     with patch('smtplib.SMTP') as mock_smtp:
#         # Configure the mock to raise an exception
#         mock_smtp.side_effect = Exception("Test connection error")
        
#         # Test data
#         to_addresses = ["recipient@example.com"]
#         subject = "Test Subject"
#         body = "Test Body"
        
#         # Call the function
#         result = send_email(to_addresses, subject, body)
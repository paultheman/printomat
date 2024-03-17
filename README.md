# Printomat
#### ** Work in progress **

![printomat-demo](https://github.com/paultheman/printomat/assets/38941045/63e95631-7f09-431c-bbda-94bd0ee13d81)

This is proof of concept implementation of a self printing service.  
The idea is to have a terminal on which you could send / upload documents or pictures and print them yourself.  
Resolution 1024x600 pixels is suited for a Raspberry Pi touch screen.  

## Functional description

The user will receive a one time password that is generated using the rand.py module. Also a QR code will be provided.  
After correctly entering the OTP the second app screen is displayed and the provided documents can be slightly edited.  

**TEST1NG** can be used as a test OTP.  

## Dependencies
- tkinter
- pymupdf
- pillow
- qrcode

Tkinter themes by [RobertJN64](https://github.com/RobertJN64/TKinterModernThemes/commits?author=RobertJN64)


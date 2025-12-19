Attribute VB_Name = "Module1"
Public Declare Sub KUnLoad Lib "KiccPos.DLL" ()
Public Declare Sub KSetOPKey Lib "KiccPos.DLL" (ByVal OkKey As Long, ByVal CancleKey As Long, ByVal SigneKey As Long)
Public Declare Function KLoad Lib "KiccPos.DLL" (ByVal pPort As Long, ByVal pBaud As Long, ByVal pErrMsg As String) As Long

Public Declare Function KOpen Lib "KiccPos.DLL" () As Long
Public Declare Function KClose Lib "KiccPos.DLL" () As Long

Public Declare Function KSaveToBmp Lib "KiccPos.DLL" (ByVal FName As String, ByVal BmpType As Long, ByVal pErrMsg As String) As Long

Public Declare Function KApproval Lib "KiccPos.DLL" (ByVal ReqType As Long, ByVal ReqMsg As String, ByVal ReqMsgLen As Long, _
 ByVal Sign As String, ByVal Emv As String, ByVal ResType As Long, ByVal ResMsg As String, ByVal ErrMsg As String, _
  ByVal KiccIP As String, ByVal KiccPort As Long, ByVal Secure As Long, ByVal RID As String, ByVal trno As String) As Long
 
 
Public Declare Function KRollBack Lib "KiccPos.DLL" (ByVal ErrMsg As String, ByVal KiccIP As String, ByVal KiccPort As Long, _
                                                     ByVal Secure As Long, ByVal RID As String) As Long
 

Public Declare Function KDownShopInfo Lib "KiccPos.DLL" ( _
             ByVal Busino As String, ByVal Areano As String, ByVal TID As String, ByVal AgentCd As String, _
             ByVal Telno As String, ByVal WaitType As Long, ByVal ErrMsg As String, _
             ByVal KiccIP As String, ByVal KiccPort As Long) As Long
             
Public Declare Function KGetShopInfo Lib "KiccPos.DLL" (ByVal TID As String, ByVal Code As String, ByVal Data As String, ByVal ErrMsg As String) As Long
Public Declare Function KClearShopInfo Lib "KiccPos.DLL" () As Long

Public Declare Function KDownDCCText Lib "KiccPos.DLL" ( _
      ByVal TID As String, ByVal KiccIP As String, ByVal KiccPort As Long, ByVal Secure As Long, ByVal ErrMsg As String) As Long
      
Public Declare Function KDownDCCTextA Lib "KiccPos.DLL" ( _
      ByVal TID As String, ByVal KiccIP As String, ByVal KiccPort As Long, ByVal Secure As Long, ByVal ErrMsg As String) As Long
      
Public Declare Function KDeleteDCCText Lib "KiccPos.DLL" () As Long
Public Declare Function KReqReset Lib "KiccPos.DLL" () As Long
Public Declare Function KReqSendRS232 Lib "KiccPos.DLL" (ByVal SendData As String, ByVal DataLen As Long, ByVal pErrMsg As String) As Long

Public Declare Function KReqCmd Lib "KiccPos.DLL" (ByVal CMD As Long, ByVal GCD As Long, ByVal JCD As Long, _
                                 ByVal SendData As String, ByVal ErrMsg As String) As Long
                                 
                                 
Public Declare Function KReqSign Lib "KiccPos.DLL" ( _
    ByVal TID As String, ByVal Amount As Long, ByVal pX As Long, ByVal pY As Long, _
    ByVal TopMsg As String, ByVal CurrCd As String, ByVal DispMsg As String, ByVal ErrMsg As String) As Long
    
Public Declare Function KReqSignA Lib "KiccPos.DLL" ( _
    ByVal TID As String, ByVal Amount As Long, ByVal pX As Long, ByVal pY As Long, _
    ByVal TopMsg As String, ByVal CurrCd As String, ByVal DispMsg As String, ByVal ErrMsg As String) As Long
    
Public Declare Function KReqSignB Lib "KiccPos.DLL" ( _
    ByVal TID As String, ByVal Amount As Long, ByVal pX As Long, ByVal pY As Long, _
    ByVal TopMsg As String, ByVal CurrCd As String, ByVal DispMsg As String, ByVal ErrMsg As String) As Long
    
   
Public Declare Function KReqSignDone Lib "KiccPos.DLL" () As Long

Public Declare Function KReqPrint Lib "KiccPos.DLL" (ByVal PrintData As String, ByVal ImgFlag As String, _
                                     ByVal ImgName As String, ByVal BmpFile As String, ByVal ErrMsg As String) As Long


Public Declare Function KReqPrint133 Lib "KiccPos.DLL" (ByVal PrintData As String, ByVal Sign As String, ByVal ErrMsg As String) As Long
Public Declare Function KReqPrint161 Lib "KiccPos.DLL" (ByVal PrintData As String, ByVal Sign As String, ByVal ErrMsg As String) As Long

Public Declare Function KWaitCmd Lib "KiccPos.DLL" ( _
    ByVal CMD As Long, ByVal RcvData As String, ByVal WaitTime As Long, ByVal WaitType As Long, _
    ByVal DispMsg As String, ByVal ErrMsg As String) As Long

Public Declare Function KWaitCmdA Lib "KiccPos.DLL" ( _
    ByVal CMD As Long, ByVal RcvData As String, ByVal ResetWaitTime As Long, ByVal WaitTime As Long, _
    ByVal WaitType As Long, ByVal DispMsg As String, ByVal ErrMsg As String) As Long

Public Declare Function KWaitCmdN Lib "KiccPos.DLL" ( _
    ByRef CMD As Long, ByRef GCD As Long, ByRef JCD As Long, ByRef RCD As Long, ByVal RcvData As String, ByVal RcvHexData As String, ByVal WaitTime As Long, _
    ByVal WaitType As Long, ByVal DispMsg As String, ByVal ErrMsg As String) As Long

Public Declare Function KWaitCmdNA Lib "KiccPos.DLL" ( _
    ByRef CMD As Long, ByRef GCD As Long, ByRef JCD As Long, ByRef RCD As Long, ByVal RcvData As String, ByVal RcvHexData As String, ByVal ResetWaitTime As Long, ByVal WaitTime As Long, _
    ByVal WaitType As Long, ByVal DispMsg As String, ByVal ErrMsg As String) As Long


Public Declare Function KGetSign Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetBmp Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetEmv Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetSeqNo Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetTID Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetCardNo Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetCardHash Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetCashNo Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetPIN Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetBF0C Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetRfFlag Lib "KiccPos.DLL" (ByVal Value As String) As Long

Public Declare Function KGetVisaClaimerText Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetVisaOfferText Lib "KiccPos.DLL" (ByVal Value As String) As Long

Public Declare Function KGetMasterClaimerText Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetMasterOfferText Lib "KiccPos.DLL" (ByVal Value As String) As Long

Public Declare Function KGetJCBClaimerText Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetJCBOfferText Lib "KiccPos.DLL" (ByVal Value As String) As Long

Public Declare Function KGetTRNO Lib "KiccPos.DLL" (ByVal RID As String, ByVal Value As String) As Long
Public Declare Function KGetVer Lib "KiccPos.DLL" (ByVal Value As String) As Long


Public Declare Function KSetSign Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KSetDebugYN Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KSetPosCd Lib "KiccPos.DLL" (ByVal PosCd As String) As Long
Public Declare Function KSetProtocol Lib "KiccPos.DLL" (ByVal Value As Long) As Long
      
Public Declare Function KGetRcvData Lib "KiccPos.DLL" (ByVal Value As String) As Long
Public Declare Function KGetRcvHexData Lib "KiccPos.DLL" (ByVal Value As String) As Long
      
Public Declare Function KGetCMD Lib "KiccPos.DLL" () As Long
Public Declare Function KGetGCD Lib "KiccPos.DLL" () As Long
Public Declare Function KGetJCD Lib "KiccPos.DLL" () As Long
Public Declare Function KGetRCD Lib "KiccPos.DLL" () As Long
      
Public Declare Function KWaitEvent Lib "KiccPos.DLL" _
     (ByRef CMD As Long, ByRef GCD As Long, ByRef JCD As Long, ByRef RCD As Long, _
      ByVal RData As String, ByVal RHexData As String, ByVal WaitTime As Long) As Long
      
      
Public Declare Function KGetEvent Lib "KiccPos.DLL" _
     (ByRef CMD As Long, ByRef GCD As Long, ByRef JCD As Long, ByRef RCD As Long, _
      ByVal RData As String, ByVal RHexData As String) As Long

Public Declare Function KDownLoad Lib "KiccPos.DLL" (ByVal FileName As String, ByVal sOption As String, ByVal ErrMsg As String) As Long








VERSION 5.00
Begin VB.Form Form1 
   Caption         =   "Form1"
   ClientHeight    =   5415
   ClientLeft      =   120
   ClientTop       =   450
   ClientWidth     =   8610
   LinkTopic       =   "Form1"
   ScaleHeight     =   5415
   ScaleWidth      =   8610
   StartUpPosition =   3  'Windows 기본값
   Begin VB.Frame Frame4 
      Caption         =   "  Event  "
      Height          =   2175
      Left            =   120
      TabIndex        =   14
      Top             =   3000
      Width           =   8295
      Begin VB.TextBox EDT_EVentHext 
         Height          =   285
         Left            =   120
         TabIndex        =   20
         Top             =   1680
         Width           =   7980
      End
      Begin VB.TextBox EDT_EVENT 
         Height          =   885
         Left            =   120
         MultiLine       =   -1  'True
         TabIndex        =   19
         Top             =   720
         Width           =   7980
      End
      Begin VB.TextBox EDT_RCD 
         Height          =   270
         Left            =   1560
         TabIndex        =   18
         Top             =   360
         Width           =   435
      End
      Begin VB.TextBox EDT_JCD 
         Height          =   270
         Left            =   1080
         TabIndex        =   17
         Top             =   360
         Width           =   435
      End
      Begin VB.TextBox EDT_GCD 
         Height          =   270
         Left            =   600
         TabIndex        =   16
         Top             =   360
         Width           =   435
      End
      Begin VB.TextBox EDT_CMDF 
         Height          =   270
         Left            =   120
         TabIndex        =   15
         Top             =   360
         Width           =   435
      End
   End
   Begin VB.Frame Frame3 
      Caption         =   "  CAT단말기요청  "
      Height          =   1455
      Left            =   120
      TabIndex        =   8
      Top             =   1440
      Width           =   8295
      Begin VB.CommandButton Command7 
         Caption         =   "단말기요청"
         Height          =   360
         Left            =   1920
         TabIndex        =   13
         Top             =   360
         Width           =   1215
      End
      Begin VB.TextBox EDT_J 
         Height          =   345
         Left            =   1320
         TabIndex        =   12
         Text            =   "04"
         Top             =   360
         Width           =   510
      End
      Begin VB.TextBox EDT_G 
         Height          =   345
         Left            =   720
         TabIndex        =   11
         Text            =   "20"
         Top             =   360
         Width           =   510
      End
      Begin VB.TextBox EDT_CMD 
         Height          =   345
         Left            =   120
         TabIndex        =   10
         Text            =   "251"
         Top             =   360
         Width           =   510
      End
      Begin VB.TextBox EDT_DATA 
         Height          =   330
         Left            =   120
         TabIndex        =   9
         Tag             =   "CD"
         Text            =   "S01=D1;S02=40;S10=1004;S23=1234567890;"
         Top             =   840
         Width           =   7980
      End
   End
   Begin VB.Frame Frame1 
      Caption         =   "   포트오픈    "
      Height          =   735
      Left            =   120
      TabIndex        =   1
      Top             =   600
      Width           =   8295
      Begin VB.CommandButton Command2 
         Caption         =   "Clear"
         Height          =   375
         Left            =   5520
         TabIndex        =   21
         Top             =   240
         Width           =   975
      End
      Begin VB.Timer Timer1 
         Enabled         =   0   'False
         Interval        =   100
         Left            =   7680
         Top             =   240
      End
      Begin VB.CommandButton Bt_DisConnect 
         Caption         =   "DisConnect"
         Height          =   345
         Left            =   4200
         TabIndex        =   7
         Top             =   240
         Width           =   1245
      End
      Begin VB.CommandButton BT_Connect 
         Caption         =   "Connect"
         Height          =   345
         Left            =   2880
         TabIndex        =   6
         Top             =   240
         Width           =   1245
      End
      Begin VB.TextBox Edt_Baud 
         Height          =   285
         Left            =   1800
         TabIndex        =   5
         Text            =   "57600"
         Top             =   360
         Width           =   885
      End
      Begin VB.TextBox EDT_PORT 
         Height          =   270
         Left            =   720
         TabIndex        =   3
         Text            =   "1"
         Top             =   360
         Width           =   420
      End
      Begin VB.Label Label3 
         Caption         =   "속도"
         Height          =   255
         Left            =   1320
         TabIndex        =   4
         Top             =   360
         Width           =   615
      End
      Begin VB.Label Label2 
         Caption         =   "포트"
         Height          =   255
         Left            =   240
         TabIndex        =   2
         Top             =   360
         Width           =   495
      End
   End
   Begin VB.Label Label1 
      Caption         =   "EP-763C / ED-785 "
      BeginProperty Font 
         Name            =   "돋움"
         Size            =   12
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   240
      TabIndex        =   0
      Top             =   120
      Width           =   2415
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub BT_Connect_Click()
Dim Err As String * 4096
Dim Ret As Long

    Ret = KLoad(Val(EDT_PORT.Text), Val(Edt_Baud.Text), Err)
    
    If Ret >= 0 Then
       Timer1.Enabled = True
    End If
    
End Sub



Private Sub Bt_DisConnect_Click()
   Timer1.Enabled = False
   KUnLoad
End Sub


Private Sub Command2_Click()
Dim Err As String * 4096
Dim Ret As Long

Ret = KReqCmd(&HFB, &H14, &H1, "", Err)

End Sub

Private Sub Command7_Click()
Dim CC As Integer
Dim GC As Integer
Dim JC As Integer
Dim sLen As Integer
Dim sData As String
Dim RData As String * 100
Dim Err As String * 4096
Dim Ret As Long

CC = Val(EDT_CMD.Text)
GC = Val(EDT_G.Text)
JC = Val(EDT_J.Text)

sData = EDT_DATA.Text
sLen = Len(sData)

Ret = KReqCmd(CC, GC, JC, sData, Err)

End Sub




Private Sub Timer1_Timer()
Dim CMD As Long
Dim GCD As Long
Dim JCD As Long
Dim RCD As Long
Dim RData As String * 4086
Dim RHexData As String * 4086

Dim Ret As Long

' KWaitCmd 명령(Blocking 방식) 을 사용하지 않고 단말기로 부터 수신되는 값을
' 채크(Non Blocking 방식)하기 위해 아래 함수를 주기적으로 호출하여 확인을 할 수 있다
' 마지막 수신된 Data 값을 리턴 받을 수 있다.

   Ret = KGetEvent(CMD, GCD, JCD, RCD, RData, RHexData)
   If Ret >= 0 Then
      EDT_CMDF.Text = Str(CMD)
      EDT_GCD.Text = Str(GCD)
      EDT_JCD.Text = Str(JCD)
      EDT_RCD.Text = Str(RCD)
      EDT_EVENT.Text = RData
      EDT_EVentHext.Text = RHexData
   End If
   
End Sub

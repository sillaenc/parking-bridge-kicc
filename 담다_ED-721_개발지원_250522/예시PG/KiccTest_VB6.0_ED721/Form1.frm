VERSION 5.00
Begin VB.Form Form1 
   Caption         =   "Form1"
   ClientHeight    =   4695
   ClientLeft      =   120
   ClientTop       =   450
   ClientWidth     =   6525
   LinkTopic       =   "Form1"
   ScaleHeight     =   4695
   ScaleWidth      =   6525
   StartUpPosition =   3  'Windows 기본값
   Begin VB.Frame Frame9 
      Caption         =   " Event  "
      Height          =   1965
      Left            =   120
      TabIndex        =   13
      Top             =   2640
      Width           =   5895
      Begin VB.TextBox EDT_EVentHext 
         Height          =   285
         Left            =   120
         TabIndex        =   19
         Top             =   1560
         Width           =   5580
      End
      Begin VB.TextBox EDT_RCD 
         Height          =   270
         Left            =   2160
         TabIndex        =   18
         Top             =   360
         Width           =   675
      End
      Begin VB.TextBox EDT_JCD 
         Height          =   270
         Left            =   1440
         TabIndex        =   17
         Top             =   360
         Width           =   675
      End
      Begin VB.TextBox EDT_GCD 
         Height          =   270
         Left            =   735
         TabIndex        =   16
         Top             =   360
         Width           =   675
      End
      Begin VB.TextBox EDT_CMDF 
         Height          =   270
         Left            =   120
         TabIndex        =   15
         Top             =   360
         Width           =   555
      End
      Begin VB.TextBox EDT_EVENT 
         Height          =   765
         Left            =   120
         MultiLine       =   -1  'True
         ScrollBars      =   2  '수직
         TabIndex        =   14
         Top             =   720
         Width           =   5580
      End
   End
   Begin VB.Frame Frame7 
      Caption         =   "Command"
      Height          =   1455
      Left            =   120
      TabIndex        =   7
      Top             =   1080
      Width           =   5895
      Begin VB.CommandButton Command7 
         Caption         =   "Send"
         Height          =   360
         Left            =   2040
         TabIndex        =   12
         Top             =   360
         Width           =   1335
      End
      Begin VB.TextBox EDT_J 
         Height          =   345
         Left            =   1305
         TabIndex        =   11
         Text            =   "04"
         Top             =   360
         Width           =   510
      End
      Begin VB.TextBox EDT_G 
         Height          =   345
         Left            =   720
         TabIndex        =   10
         Text            =   "14"
         Top             =   360
         Width           =   510
      End
      Begin VB.TextBox EDT_CMD 
         Height          =   345
         Left            =   120
         TabIndex        =   9
         Text            =   "FB"
         Top             =   360
         Width           =   510
      End
      Begin VB.TextBox EDT_DATA 
         Height          =   330
         Left            =   120
         TabIndex        =   8
         Tag             =   "CD"
         Text            =   "S01=D1;S02=40;S10=1004;"
         Top             =   960
         Width           =   5580
      End
      Begin VB.Timer Timer1 
         Enabled         =   0   'False
         Interval        =   50
         Left            =   0
         Top             =   0
      End
   End
   Begin VB.Frame Frame2 
      Caption         =   "Common"
      Height          =   885
      Left            =   120
      TabIndex        =   0
      Top             =   120
      Width           =   5895
      Begin VB.TextBox EDT_PORT 
         Height          =   270
         Left            =   600
         TabIndex        =   4
         Text            =   "1"
         Top             =   285
         Width           =   420
      End
      Begin VB.TextBox Edt_Baud 
         Height          =   285
         Left            =   1665
         TabIndex        =   3
         Text            =   "57600"
         Top             =   285
         Width           =   750
      End
      Begin VB.CommandButton BT_Connect 
         Caption         =   "Connect"
         Height          =   345
         Left            =   2520
         TabIndex        =   2
         Top             =   255
         Width           =   1245
      End
      Begin VB.CommandButton Bt_DisConnect 
         Caption         =   "DisConnect"
         Height          =   345
         Left            =   3840
         TabIndex        =   1
         Top             =   255
         Width           =   1245
      End
      Begin VB.Label Label1 
         Caption         =   "포트"
         Height          =   255
         Left            =   180
         TabIndex        =   6
         Top             =   345
         Width           =   465
      End
      Begin VB.Label Label2 
         Caption         =   "속도"
         Height          =   315
         Left            =   1125
         TabIndex        =   5
         Top             =   330
         Width           =   690
      End
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

Private Sub Command7_Click()
Dim CC As Integer
Dim GC As Integer
Dim JC As Integer
Dim sLen As Integer
Dim sData As String
Dim RData As String * 100
Dim Err As String * 4096
Dim Ret As Long

    
    CC = Val("&H0" & EDT_CMD.Text)
    GC = Val("&H0" & EDT_G.Text)
    JC = Val("&H0" & EDT_J.Text)
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
Dim SignData As String * 2048
Dim EmvData As String * 1024
Dim Ret As Long

   Ret = KGetEvent(CMD, GCD, JCD, RCD, RData, RHexData)
   If Ret >= 0 Then
      EDT_CMDF.Text = Hex(CMD)
      EDT_GCD.Text = Hex(GCD)
      EDT_JCD.Text = Hex(JCD)
      EDT_RCD.Text = Hex(RCD)
      EDT_EVENT.Text = RData
      EDT_EVentHext.Text = RHexData
      
      
   End If
   
End Sub

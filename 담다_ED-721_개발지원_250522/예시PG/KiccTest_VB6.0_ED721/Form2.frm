VERSION 5.00
Begin VB.Form Form2 
   Caption         =   "Form2"
   ClientHeight    =   2820
   ClientLeft      =   120
   ClientTop       =   450
   ClientWidth     =   5895
   LinkTopic       =   "Form2"
   ScaleHeight     =   2820
   ScaleWidth      =   5895
   StartUpPosition =   3  'Windows 기본값
   Begin VB.Frame Frame1 
      Height          =   2700
      Left            =   0
      TabIndex        =   0
      Top             =   0
      Width           =   5805
      Begin VB.TextBox EDT_DOWNIP 
         Height          =   285
         Left            =   1275
         MaxLength       =   15
         TabIndex        =   12
         Text            =   "203.233.72.55"
         Top             =   2080
         Width           =   1755
      End
      Begin VB.TextBox EDT_BUSINO 
         Height          =   285
         Left            =   1275
         MaxLength       =   10
         TabIndex        =   6
         Text            =   "1168119948"
         Top             =   225
         Width           =   1755
      End
      Begin VB.TextBox EDT_AREA 
         Height          =   285
         Left            =   1275
         MaxLength       =   3
         TabIndex        =   5
         Text            =   "02"
         Top             =   615
         Width           =   1755
      End
      Begin VB.TextBox EDT_TID 
         Height          =   285
         Left            =   1275
         MaxLength       =   10
         TabIndex        =   4
         Text            =   "0700081"
         Top             =   975
         Width           =   1755
      End
      Begin VB.TextBox EDT_AGENT 
         Height          =   285
         Left            =   1275
         MaxLength       =   4
         TabIndex        =   3
         Text            =   "1000"
         Top             =   1350
         Width           =   1755
      End
      Begin VB.TextBox EDT_TELNO 
         Height          =   285
         Left            =   1275
         MaxLength       =   15
         TabIndex        =   2
         Text            =   "0216001234"
         Top             =   1725
         Width           =   1755
      End
      Begin VB.CommandButton Command1 
         Caption         =   "정보수신"
         Height          =   465
         Left            =   3525
         TabIndex        =   1
         Top             =   225
         Width           =   1725
      End
      Begin VB.Label Label1 
         Caption         =   "IP"
         Height          =   180
         Index           =   5
         Left            =   240
         TabIndex        =   13
         Top             =   2160
         Width           =   900
      End
      Begin VB.Label Label1 
         Caption         =   "사업자번호 "
         Height          =   180
         Index           =   0
         Left            =   195
         TabIndex        =   11
         Top             =   285
         Width           =   960
      End
      Begin VB.Label Label1 
         Caption         =   "지역코드 "
         Height          =   180
         Index           =   1
         Left            =   180
         TabIndex        =   10
         Top             =   645
         Width           =   960
      End
      Begin VB.Label Label1 
         Caption         =   "TID"
         Height          =   180
         Index           =   2
         Left            =   195
         TabIndex        =   9
         Top             =   1020
         Width           =   960
      End
      Begin VB.Label Label1 
         Caption         =   "POS 코드"
         Height          =   180
         Index           =   3
         Left            =   210
         TabIndex        =   8
         Top             =   1350
         Width           =   960
      End
      Begin VB.Label Label1 
         Caption         =   "전화번호"
         Height          =   180
         Index           =   4
         Left            =   180
         TabIndex        =   7
         Top             =   1725
         Width           =   960
      End
   End
End
Attribute VB_Name = "Form2"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub Command1_Click()
Dim Ret As Integer
Dim sE As String * 1024

   Ret = KDownShopInfo(EDT_BUSINO.Text, EDT_AREA.Text, EDT_TID.Text, EDT_AGENT.Text, _
                        EDT_TELNO.Text, 0, sE, EDT_DOWNIP.Text, 4110)
   
   If Ret = 0 Then
      MsgBox "Success"
   Else
      MsgBox Val(Ret) & "/" & sE
   End If

End Sub


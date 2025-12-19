object Form1: TForm1
  Left = 476
  Top = 230
  Width = 538
  Height = 463
  Caption = 'Form1'
  Color = clBtnFace
  Constraints.MinWidth = 130
  Font.Charset = DEFAULT_CHARSET
  Font.Color = clWindowText
  Font.Height = -11
  Font.Name = 'MS Sans Serif'
  Font.Style = []
  OldCreateOrder = False
  Position = poScreenCenter
  Scaled = False
  PixelsPerInch = 96
  TextHeight = 13
  object GroupBox1: TGroupBox
    Left = 8
    Top = 8
    Width = 489
    Height = 57
    Caption = 'Common'
    TabOrder = 0
    object Label1: TLabel
      Left = 16
      Top = 16
      Width = 30
      Height = 13
      Caption = 'PORT'
    end
    object Label2: TLabel
      Left = 88
      Top = 16
      Width = 36
      Height = 13
      Caption = 'SPEED'
    end
    object Edit1: TEdit
      Left = 49
      Top = 13
      Width = 24
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 0
      Text = '1'
    end
    object Edit2: TEdit
      Left = 129
      Top = 13
      Width = 48
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 1
      Text = '57600'
    end
    object Button1: TButton
      Left = 184
      Top = 11
      Width = 73
      Height = 25
      Caption = 'Connect'
      TabOrder = 2
      OnClick = Button1Click
    end
    object Button2: TButton
      Left = 264
      Top = 11
      Width = 73
      Height = 25
      Caption = 'DisConnect'
      TabOrder = 3
      OnClick = Button2Click
    end
  end
  object GroupBox4: TGroupBox
    Left = 8
    Top = 176
    Width = 489
    Height = 177
    Caption = 'Event'
    TabOrder = 1
    object evt_cmd: TEdit
      Left = 16
      Top = 24
      Width = 57
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 0
    end
    object evt_gcd: TEdit
      Left = 80
      Top = 24
      Width = 57
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 1
    end
    object evt_jcd: TEdit
      Left = 144
      Top = 24
      Width = 57
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 2
    end
    object evt_rcd: TEdit
      Left = 208
      Top = 24
      Width = 57
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 3
    end
    object evt_rdata: TMemo
      Left = 16
      Top = 48
      Width = 449
      Height = 57
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 4
    end
    object evt_rhexdata: TMemo
      Left = 16
      Top = 112
      Width = 449
      Height = 57
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 5
    end
  end
  object GroupBox7: TGroupBox
    Left = 8
    Top = 72
    Width = 489
    Height = 97
    Caption = 'Command'
    TabOrder = 2
    object edt_cmd: TEdit
      Left = 16
      Top = 24
      Width = 41
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 0
      Text = 'FB'
    end
    object edt_gcd: TEdit
      Left = 64
      Top = 24
      Width = 41
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 1
      Text = '14'
    end
    object edt_jcd: TEdit
      Left = 112
      Top = 24
      Width = 41
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 2
      Text = '04'
    end
    object edt_data: TEdit
      Left = 16
      Top = 56
      Width = 433
      Height = 21
      ImeName = 'Microsoft Office IME 2007'
      TabOrder = 3
      Text = 'S01=D1;S02=40;S10=1004;'
    end
    object bt_cmdsend: TButton
      Left = 168
      Top = 24
      Width = 113
      Height = 25
      Caption = 'ReqCmd '#50836#52397
      TabOrder = 4
      OnClick = bt_cmdsendClick
    end
  end
  object Timer1: TTimer
    Enabled = False
    Interval = 100
    OnTimer = Timer1Timer
    Left = 352
    Top = 16
  end
end

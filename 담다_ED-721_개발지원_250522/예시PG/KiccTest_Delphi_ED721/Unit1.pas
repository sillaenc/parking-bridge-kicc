unit Unit1;

interface

uses
  Windows, Messages, SysUtils, Classes, Graphics, Controls, Forms, Dialogs,
  StdCtrls, ExtCtrls;

type
  TForm1 = class(TForm)
    GroupBox1: TGroupBox;
    Label1: TLabel;
    Label2: TLabel;
    Edit1: TEdit;
    Edit2: TEdit;
    Button1: TButton;
    Button2: TButton;
    GroupBox4: TGroupBox;
    evt_cmd: TEdit;
    evt_gcd: TEdit;
    evt_jcd: TEdit;
    evt_rcd: TEdit;
    evt_rdata: TMemo;
    evt_rhexdata: TMemo;
    GroupBox7: TGroupBox;
    edt_cmd: TEdit;
    edt_gcd: TEdit;
    edt_jcd: TEdit;
    edt_data: TEdit;
    bt_cmdsend: TButton;
    Timer1: TTimer;
    procedure Button1Click(Sender: TObject);
    procedure Button2Click(Sender: TObject);
    procedure bt_cmdsendClick(Sender: TObject);
    procedure Timer1Timer(Sender: TObject);
  private
    { Private declarations }
  public
    { Public declarations }
  end;

var
  Form1: TForm1;
  multiflag : boolean;

implementation

    procedure KUnLoad (); stdcall; external 'KiccPos.Dll' name 'KUnLoad';
    function KLoad (pPort:Integer; pBaud:Integer; pErrMsg : pChar):integer; stdcall; external 'KiccPos.Dll' name 'KLoad';
    function KReqCmd (CMD, GCD, JCD : Integer; SendData, ErrMsg : pChar) :integer ;stdcall; external 'KiccPos.Dll' name 'KReqCmd';
    function KGetEvent (var CMD : Integer; var GCD : Integer; var JCD : Integer; var RCD : Integer; RData, RHexData : pChar) :integer ;stdcall; external 'KiccPos.Dll' name 'KGetEvent';

{$R *.DFM}

function HexToInt(lsData : string) : integer;
var lnTemp : integer;
    lsTemp : string;
begin

   lsTemp := UpperCase(lsData);

   if ord(lsTemp[1]) >= 65 then
     lnTemp := (ord(lsTemp[1]) - 55) * 16
   else
     lnTemp := (ord(lsTemp[1]) - 48) * 16;

   if ord(lsTemp[2]) >= 65 then
     lnTemp := lnTemp + (ord(lsTemp[2]) - 55)
   else
     lnTemp := lnTemp + (ord(lsTemp[2]) - 48);

   result := lnTemp;

end;



procedure TForm1.Button1Click(Sender: TObject);
var
    Err : pChar;
    Ret : integer;
begin
    getmem(Err,4096);
    try
        Ret := KLoad(strtoint(Edit1.Text), strtoint(Edit2.Text), Err);
        Timer1.Enabled := true;
    finally
        freeMem(Err);
    end;
end;

procedure TForm1.Button2Click(Sender: TObject);
begin
    Timer1.Enabled := false;
    KUnLoad;
end;

procedure TForm1.bt_cmdsendClick(Sender: TObject);
var
    Err,rData : pChar;
    Ret : integer;
begin
    getmem(Err,4096);
    getmem(rData,4096);
  
    try
        Ret := KReqCmd(HexToInt(edt_cmd.Text), HexToInt(edt_gcd.Text), HexToInt(edt_jcd.Text), pChar(edt_data.Text), Err);
    finally
        freeMem(Err);
        freeMem(rData);
    end;

end;

procedure TForm1.Timer1Timer(Sender: TObject);
var
    RHex : pChar;
    Recv : pChar;
    CMD, GCD, JCD, RCD : integer;
    Ret : integer;
begin
    getmem(RHex,4096);
    getmem(Recv,4096);
    try
        Ret := KGetEvent(CMD, GCD, JCD, RCD, Recv, RHex);
        if(Ret >= 0 )then begin
            evt_cmd.Text := IntToHex(CMD, 2);
            evt_gcd.Text := IntToHex(GCD, 2);
            evt_jcd.Text := IntToHex(JCD, 2);
            evt_rcd.Text := IntToHex(RCD, 2);
            evt_rdata.Lines.Clear;
            evt_rhexdata.Lines.Clear;
            evt_rdata.Lines.Add(Recv);
            evt_rdata.Perform(WM_VSCROLL, SB_TOP, 0);
            evt_rhexdata.Lines.Add(RHex);
            evt_rhexdata.Perform(WM_VSCROLL, SB_TOP, 0);
        end;
    finally
        freeMem(RHex);
        freeMem(Recv);
    end;
end;

end.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.IO;
using System.Threading;



namespace KiccTest
{
   
    public partial class Form1 : Form
    {
        bool multiflag = false;
        
        [DllImport("KiccPos.dll", EntryPoint = "KLoad", CharSet = CharSet.Ansi)]
        private static extern int KLoad(int pPort, int pBaud, byte[] pErrMsg);

        [DllImport("KiccPos.dll", EntryPoint = "KUnLoad", CharSet = CharSet.Ansi)]
        private static extern void KUnLoad();

        [DllImport("KiccPos.dll", EntryPoint = "KReqReset", CharSet = CharSet.Ansi)]
        private static extern int KReqReset();

        [DllImport("KiccPos.dll", EntryPoint = "KReqSign", CharSet = CharSet.Ansi)]
        private static extern int KReqSign(String TID, int Amount, int pX, int pY,
            String TopMsg, String CurrCD, String DispMsg, byte[] ErrMsg);

        [DllImport("KiccPos.dll", EntryPoint = "KReqSignA", CharSet = CharSet.Ansi)]
        private static extern int KReqSignA(String TID, int Amount, int pX, int pY,
            String TopMsg, String CurrCD, String DispMsg, byte[] ErrMsg);

        [DllImport("KiccPos.dll", EntryPoint = "KSaveToBmp", CharSet = CharSet.Ansi)]
        private static extern int KSaveToBmp(String FName, int BmpType, byte[] ErrMsg);

        [DllImport("KiccPos.dll", EntryPoint = "KReqCmd", CharSet = CharSet.Ansi)]
        private static extern int KReqCmd(int CMD, int GCD, int JCD, String SendData, byte[] ErrMsg);

        [DllImport("KiccPos.dll", EntryPoint = "KWaitCmd", CharSet = CharSet.Ansi)]
        private static extern int KWaitCmd(int CMD, byte[] RcvData, int WaitTime, int WaitType, String DispMsg, byte[] ErrMsg);

        [DllImport("KiccPos.dll", EntryPoint = "KDownShopInfo", CharSet = CharSet.Ansi)]
        private static extern int KDownShopInfo(String Busino, String Areano, String TID, String AgentCd,
            String Telno, int WaitType, byte[] ErrMsg, String KiccIP, int KiccPort);

        [DllImport("KiccPos.dll", EntryPoint = "KGetSign", CharSet = CharSet.Ansi)]
        private static extern int KGetSign(byte[] Sign);

        [DllImport("KiccPos.dll", EntryPoint = "KGetEmv", CharSet = CharSet.Ansi)]
        private static extern int KGetEmv(byte[] Emv);

        [DllImport("KiccPos.dll", EntryPoint = "KApproval", CharSet = CharSet.Ansi)]
        private static extern int KApproval(int ReqType, String ReqMsg, int ReqMsgLen,
            String Sign, String Emv, int ResType, byte[] ResMsg, byte[] ErrMsg,
            String KiccIP, int KiccPort, int Secure, String RID, String trno);

        [DllImport("KiccPos.dll", EntryPoint = "KGetTRNO", CharSet = CharSet.Ansi)]
        private static extern int KGetTRNO(String RID, byte[] trno);

        [DllImport("KiccPos.dll", EntryPoint = "KRollBackA", CharSet = CharSet.Ansi)]
        private static extern int KRollBackA(byte[] ErrMsg, String KiccIP, int KiccPort, int Secure, String RID, String trno);
        

        [DllImport("KiccPos.dll", EntryPoint = "KGetCardNo", CharSet = CharSet.Ansi)]
        private static extern int KGetCardNo(byte[] RCARD);

        [DllImport("KiccPos.dll", EntryPoint = "KGetCashNo", CharSet = CharSet.Ansi)]
        private static extern int KGetCashNo(byte[] RCASH);
        
        [DllImport("KiccPos.dll", EntryPoint = "KGetEvent", CharSet = CharSet.Ansi)]
        private static extern int KGetEvent(ref int CMD, ref int GCD, ref int JCD, ref int RCD, byte[] RData, byte[] RHexData);

        [DllImport("KiccPos.dll", EntryPoint = "KGetCardHash", CharSet = CharSet.Ansi)]
        private static extern int KGetCardHash(byte[] RCASH);

        [DllImport("KiccPos.dll", EntryPoint = "KDecodingCardHash", CharSet = CharSet.Ansi)]
        private static extern int KDecodingCardHash(String sRndKey, String sEncodingCardHash, byte[] sDecodingCardHash, byte[] ErrMSg);

        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
        }


        

        private void button1_Click(object sender, EventArgs e)
        {
            byte[] err = new byte[4096];
            int ret = 0;

            ret = KLoad(int.Parse(textBox1.Text), int.Parse(textBox2.Text), err);

            if (ret >= 0)
            {
                MessageBox.Show("OPEN");
                //timer1.Enabled = true;
            }
        }

        private void button2_Click(object sender, EventArgs e)
        {
            KUnLoad();
            timer1.Enabled = false;
        }
        
        private void button3_Click(object sender, EventArgs e)
        {
            int ret = 0;
            
            ret = KReqReset();
        
        }

        private void button4_Click(object sender, EventArgs e)
        {
            byte[] err = new byte[4096];
            int ret = 0;

            ret = KReqSign("0700081", 1000, 100, 100, "", "", "", err);

            if (ret >= 0)
            {
                ret = KSaveToBmp(".\\Sign.bmp", 0, err);
            }

        }

        private void button5_Click(object sender, EventArgs e)
        {
            byte[] err = new byte[4096];
            byte[] pCash = new byte[20];
            int ret = 0;

            ret = KReqCmd(Convert.ToInt32("C3", 16), 0, 0, "", err);

            ret = KWaitCmd(Convert.ToInt32("C5", 16), pCash, 0, 2, "현금 영수증 번호를 입력해 주세요", err);

            if (ret > 0)
                MessageBox.Show(System.Text.Encoding.Default.GetString(pCash));
        }


       

        private void getSign()
        {
            byte[] err = new byte[1024];
            byte[] Sign = new byte[2048];
            int ret = 0;

            ret = KGetSign(Sign);

            if (ret >= 0)
            {
                et_sign.Text = System.Text.Encoding.Default.GetString(Sign);
               
            }

        }

      

    

       


        private void button12_Click(object sender, EventArgs e)
        {
            multiflag = false;

            byte[] err = new byte[4096];
            int ret = 0;
            et_event_rdata.Text = "";
            ret = KReqCmd(Convert.ToInt32(et_cmd_cmd.Text, 16), Convert.ToInt32(et_cmd_gcd.Text, 16), Convert.ToInt32(et_cmd_jcd.Text, 16), et_cmd_data.Text, err);

        }

        private void timer1_Tick(object sender, EventArgs e)
        {
            int CMD = 0;
            int GCD = 0;
            int JCD = 0;
            int RCD = 0;              
            int ret = 0;
            byte[] RData = new byte[2048];
            byte[] RHexData = new byte[4096];

            String Secudata;

            ret = KGetEvent(ref CMD, ref GCD, ref JCD, ref RCD, RData, RHexData);
            
            if (ret > 0)
            {
                et_event_cmd.Text = CMD.ToString("X2");
                et_event_gcd.Text = GCD.ToString("X2");
                et_event_jcd.Text = JCD.ToString("X2");
                et_event_rcd.Text = RCD.ToString("X2");
                et_event_rdata.Text = System.Text.Encoding.Default.GetString(RData);
                et_event_rhexdata.Text = System.Text.Encoding.Default.GetString(RHexData);

                
                if (CMD.ToString("X2") == "A7" && RCD.ToString("X2") == "00")
                {
                    getSign();
                }
            }

        }

      
    

      

     

        
      


      

     

        public static byte[] HexStringToBytes(string hexString)
        {
            if (hexString == null)
                throw new ArgumentNullException("hexString");
            if (hexString.Length % 2 != 0)
                throw new ArgumentException("hexString must have an even length", "hexString");
            var bytes = new byte[hexString.Length / 2];
            for (int i = 0; i < bytes.Length; i++)
            {
                string currentHex = hexString.Substring(i * 2, 2);
                bytes[i] = Convert.ToByte(currentHex, 16);
            }
            return bytes;
        }

       
        private static string Decrypt(byte[] EncryptArray, byte[] KeyArray)
        {
            //byte[] KeyArray = UTF8Encoding.UTF8.GetBytes(key);
            //byte[] EncryptArray = HexToByte(s);
            //byte[] EncryptArray = UTF8Encoding.UTF8.GetBytes(s);
            RijndaelManaged Rdel = new RijndaelManaged();
            Rdel.Mode = CipherMode.ECB;
            Rdel.Padding = PaddingMode.Zeros;
            Rdel.Key = KeyArray;

            ICryptoTransform CtransForm = Rdel.CreateDecryptor();
            byte[] ResultArray = CtransForm.TransformFinalBlock(EncryptArray, 0, EncryptArray.Length);
            return UTF8Encoding.UTF8.GetString(ResultArray);
        }

       

    

      

      

        

     
      

       

    }

}

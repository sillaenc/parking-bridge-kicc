namespace KiccTest
{
    partial class Form1
    {
        /// <summary>
        /// 필수 디자이너 변수입니다.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// 사용 중인 모든 리소스를 정리합니다.
        /// </summary>
        /// <param name="disposing">관리되는 리소스를 삭제해야 하면 true이고, 그렇지 않으면 false입니다.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form 디자이너에서 생성한 코드

        /// <summary>
        /// 디자이너 지원에 필요한 메서드입니다.
        /// 이 메서드의 내용을 코드 편집기로 수정하지 마십시오.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            this.label1 = new System.Windows.Forms.Label();
            this.textBox1 = new System.Windows.Forms.TextBox();
            this.textBox2 = new System.Windows.Forms.TextBox();
            this.label2 = new System.Windows.Forms.Label();
            this.button1 = new System.Windows.Forms.Button();
            this.button2 = new System.Windows.Forms.Button();
            this.groupBox1 = new System.Windows.Forms.GroupBox();
            this.et_cmd_jcd = new System.Windows.Forms.TextBox();
            this.et_cmd_gcd = new System.Windows.Forms.TextBox();
            this.et_cmd_cmd = new System.Windows.Forms.TextBox();
            this.button12 = new System.Windows.Forms.Button();
            this.et_cmd_data = new System.Windows.Forms.TextBox();
            this.timer1 = new System.Windows.Forms.Timer(this.components);
            this.groupBox2 = new System.Windows.Forms.GroupBox();
            this.et_sign = new System.Windows.Forms.TextBox();
            this.groupBox3 = new System.Windows.Forms.GroupBox();
            this.et_emv = new System.Windows.Forms.TextBox();
            this.groupBox6 = new System.Windows.Forms.GroupBox();
            this.et_event_rhexdata = new System.Windows.Forms.TextBox();
            this.et_event_rdata = new System.Windows.Forms.TextBox();
            this.et_event_rcd = new System.Windows.Forms.TextBox();
            this.et_event_jcd = new System.Windows.Forms.TextBox();
            this.et_event_gcd = new System.Windows.Forms.TextBox();
            this.et_event_cmd = new System.Windows.Forms.TextBox();
            this.groupBox1.SuspendLayout();
            this.groupBox2.SuspendLayout();
            this.groupBox3.SuspendLayout();
            this.groupBox6.SuspendLayout();
            this.SuspendLayout();
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(12, 15);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(29, 12);
            this.label1.TabIndex = 0;
            this.label1.Text = "포트";
            // 
            // textBox1
            // 
            this.textBox1.Location = new System.Drawing.Point(47, 12);
            this.textBox1.MaxLength = 2;
            this.textBox1.Name = "textBox1";
            this.textBox1.Size = new System.Drawing.Size(35, 21);
            this.textBox1.TabIndex = 1;
            this.textBox1.Text = "1";
            // 
            // textBox2
            // 
            this.textBox2.Location = new System.Drawing.Point(123, 12);
            this.textBox2.MaxLength = 6;
            this.textBox2.Name = "textBox2";
            this.textBox2.Size = new System.Drawing.Size(57, 21);
            this.textBox2.TabIndex = 3;
            this.textBox2.Text = "115200";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(88, 15);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(29, 12);
            this.label2.TabIndex = 2;
            this.label2.Text = "속도";
            // 
            // button1
            // 
            this.button1.Location = new System.Drawing.Point(186, 12);
            this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(89, 20);
            this.button1.TabIndex = 4;
            this.button1.Text = "Connect";
            this.button1.UseVisualStyleBackColor = true;
            this.button1.Click += new System.EventHandler(this.button1_Click);
            // 
            // button2
            // 
            this.button2.Location = new System.Drawing.Point(281, 12);
            this.button2.Name = "button2";
            this.button2.Size = new System.Drawing.Size(89, 20);
            this.button2.TabIndex = 5;
            this.button2.Text = "DisConnect";
            this.button2.UseVisualStyleBackColor = true;
            this.button2.Click += new System.EventHandler(this.button2_Click);
            // 
            // groupBox1
            // 
            this.groupBox1.Controls.Add(this.et_cmd_jcd);
            this.groupBox1.Controls.Add(this.et_cmd_gcd);
            this.groupBox1.Controls.Add(this.et_cmd_cmd);
            this.groupBox1.Controls.Add(this.button12);
            this.groupBox1.Controls.Add(this.et_cmd_data);
            this.groupBox1.Location = new System.Drawing.Point(14, 93);
            this.groupBox1.Name = "groupBox1";
            this.groupBox1.Size = new System.Drawing.Size(1064, 103);
            this.groupBox1.TabIndex = 21;
            this.groupBox1.TabStop = false;
            this.groupBox1.Text = "Command";
            // 
            // et_cmd_jcd
            // 
            this.et_cmd_jcd.Location = new System.Drawing.Point(114, 67);
            this.et_cmd_jcd.Name = "et_cmd_jcd";
            this.et_cmd_jcd.Size = new System.Drawing.Size(41, 21);
            this.et_cmd_jcd.TabIndex = 27;
            this.et_cmd_jcd.Text = "04";
            // 
            // et_cmd_gcd
            // 
            this.et_cmd_gcd.Location = new System.Drawing.Point(67, 67);
            this.et_cmd_gcd.Name = "et_cmd_gcd";
            this.et_cmd_gcd.Size = new System.Drawing.Size(41, 21);
            this.et_cmd_gcd.TabIndex = 26;
            this.et_cmd_gcd.Text = "14";
            // 
            // et_cmd_cmd
            // 
            this.et_cmd_cmd.Location = new System.Drawing.Point(20, 67);
            this.et_cmd_cmd.Name = "et_cmd_cmd";
            this.et_cmd_cmd.Size = new System.Drawing.Size(41, 21);
            this.et_cmd_cmd.TabIndex = 25;
            this.et_cmd_cmd.Text = "FB";
            // 
            // button12
            // 
            this.button12.Location = new System.Drawing.Point(965, 67);
            this.button12.Name = "button12";
            this.button12.Size = new System.Drawing.Size(75, 23);
            this.button12.TabIndex = 17;
            this.button12.Text = "ReqCmd";
            this.button12.UseVisualStyleBackColor = true;
            this.button12.Click += new System.EventHandler(this.button12_Click);
            // 
            // et_cmd_data
            // 
            this.et_cmd_data.Location = new System.Drawing.Point(161, 67);
            this.et_cmd_data.MaxLength = 1024;
            this.et_cmd_data.Name = "et_cmd_data";
            this.et_cmd_data.Size = new System.Drawing.Size(759, 21);
            this.et_cmd_data.TabIndex = 16;
            this.et_cmd_data.Text = "S01=D1;S02=40;S10=1004;";
            // 
            // timer1
            // 
            this.timer1.Enabled = true;
            this.timer1.Tick += new System.EventHandler(this.timer1_Tick);
            // 
            // groupBox2
            // 
            this.groupBox2.Controls.Add(this.et_sign);
            this.groupBox2.Location = new System.Drawing.Point(14, 291);
            this.groupBox2.Name = "groupBox2";
            this.groupBox2.Size = new System.Drawing.Size(520, 112);
            this.groupBox2.TabIndex = 22;
            this.groupBox2.TabStop = false;
            this.groupBox2.Text = "SignData";
            // 
            // et_sign
            // 
            this.et_sign.Location = new System.Drawing.Point(20, 26);
            this.et_sign.Multiline = true;
            this.et_sign.Name = "et_sign";
            this.et_sign.ScrollBars = System.Windows.Forms.ScrollBars.Vertical;
            this.et_sign.Size = new System.Drawing.Size(478, 65);
            this.et_sign.TabIndex = 0;
            // 
            // groupBox3
            // 
            this.groupBox3.Controls.Add(this.et_emv);
            this.groupBox3.Location = new System.Drawing.Point(556, 291);
            this.groupBox3.Name = "groupBox3";
            this.groupBox3.Size = new System.Drawing.Size(522, 112);
            this.groupBox3.TabIndex = 23;
            this.groupBox3.TabStop = false;
            this.groupBox3.Text = "EmvData";
            // 
            // et_emv
            // 
            this.et_emv.Location = new System.Drawing.Point(20, 26);
            this.et_emv.Multiline = true;
            this.et_emv.Name = "et_emv";
            this.et_emv.ScrollBars = System.Windows.Forms.ScrollBars.Vertical;
            this.et_emv.Size = new System.Drawing.Size(478, 65);
            this.et_emv.TabIndex = 0;
            // 
            // groupBox6
            // 
            this.groupBox6.Controls.Add(this.et_event_rhexdata);
            this.groupBox6.Controls.Add(this.et_event_rdata);
            this.groupBox6.Controls.Add(this.et_event_rcd);
            this.groupBox6.Controls.Add(this.et_event_jcd);
            this.groupBox6.Controls.Add(this.et_event_gcd);
            this.groupBox6.Controls.Add(this.et_event_cmd);
            this.groupBox6.Location = new System.Drawing.Point(14, 202);
            this.groupBox6.Name = "groupBox6";
            this.groupBox6.Size = new System.Drawing.Size(1064, 83);
            this.groupBox6.TabIndex = 26;
            this.groupBox6.TabStop = false;
            this.groupBox6.Text = "Event";
            // 
            // et_event_rhexdata
            // 
            this.et_event_rhexdata.Location = new System.Drawing.Point(208, 47);
            this.et_event_rhexdata.Name = "et_event_rhexdata";
            this.et_event_rhexdata.Size = new System.Drawing.Size(832, 21);
            this.et_event_rhexdata.TabIndex = 33;
            // 
            // et_event_rdata
            // 
            this.et_event_rdata.Location = new System.Drawing.Point(208, 20);
            this.et_event_rdata.Name = "et_event_rdata";
            this.et_event_rdata.Size = new System.Drawing.Size(832, 21);
            this.et_event_rdata.TabIndex = 32;
            // 
            // et_event_rcd
            // 
            this.et_event_rcd.Location = new System.Drawing.Point(161, 20);
            this.et_event_rcd.Name = "et_event_rcd";
            this.et_event_rcd.Size = new System.Drawing.Size(41, 21);
            this.et_event_rcd.TabIndex = 31;
            // 
            // et_event_jcd
            // 
            this.et_event_jcd.Location = new System.Drawing.Point(114, 20);
            this.et_event_jcd.Name = "et_event_jcd";
            this.et_event_jcd.Size = new System.Drawing.Size(41, 21);
            this.et_event_jcd.TabIndex = 30;
            // 
            // et_event_gcd
            // 
            this.et_event_gcd.Location = new System.Drawing.Point(67, 20);
            this.et_event_gcd.Name = "et_event_gcd";
            this.et_event_gcd.Size = new System.Drawing.Size(41, 21);
            this.et_event_gcd.TabIndex = 29;
            // 
            // et_event_cmd
            // 
            this.et_event_cmd.Location = new System.Drawing.Point(20, 20);
            this.et_event_cmd.Name = "et_event_cmd";
            this.et_event_cmd.Size = new System.Drawing.Size(41, 21);
            this.et_event_cmd.TabIndex = 28;
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1093, 490);
            this.Controls.Add(this.groupBox6);
            this.Controls.Add(this.groupBox3);
            this.Controls.Add(this.groupBox2);
            this.Controls.Add(this.groupBox1);
            this.Controls.Add(this.button2);
            this.Controls.Add(this.button1);
            this.Controls.Add(this.textBox2);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.textBox1);
            this.Controls.Add(this.label1);
            this.Name = "Form1";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Form1";
            this.Load += new System.EventHandler(this.Form1_Load);
            this.groupBox1.ResumeLayout(false);
            this.groupBox1.PerformLayout();
            this.groupBox2.ResumeLayout(false);
            this.groupBox2.PerformLayout();
            this.groupBox3.ResumeLayout(false);
            this.groupBox3.PerformLayout();
            this.groupBox6.ResumeLayout(false);
            this.groupBox6.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.TextBox textBox1;
        private System.Windows.Forms.TextBox textBox2;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Button button1;
        private System.Windows.Forms.Button button2;
        private System.Windows.Forms.GroupBox groupBox1;
        private System.Windows.Forms.TextBox et_cmd_data;
        private System.Windows.Forms.Button button12;
        private System.Windows.Forms.Timer timer1;
        private System.Windows.Forms.TextBox et_cmd_jcd;
        private System.Windows.Forms.TextBox et_cmd_gcd;
        private System.Windows.Forms.TextBox et_cmd_cmd;
        private System.Windows.Forms.GroupBox groupBox2;
        private System.Windows.Forms.TextBox et_sign;
        private System.Windows.Forms.GroupBox groupBox3;
        private System.Windows.Forms.TextBox et_emv;
        private System.Windows.Forms.GroupBox groupBox6;
        private System.Windows.Forms.TextBox et_event_rdata;
        private System.Windows.Forms.TextBox et_event_rcd;
        private System.Windows.Forms.TextBox et_event_jcd;
        private System.Windows.Forms.TextBox et_event_gcd;
        private System.Windows.Forms.TextBox et_event_cmd;
        private System.Windows.Forms.TextBox et_event_rhexdata;
    }
}


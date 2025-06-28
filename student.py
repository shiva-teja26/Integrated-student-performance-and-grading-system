from tkinter import *
import sqlite3
import time

def clickok():
    con=sqlite3.connect('studentrecords.db')
    c=con.cursor()
    num=e.get()
    num=int(num)
    print(num)
    try:
        c.execute(f'DELETE FROM StudentData WHERE Roll={num}')
        con.commit()
        button.config(command=lambda:button.pack_forget())
        l2=Label(deletewin,fg="red",text="Deleted Successfully",font=("Helvetica",10)).place(x=6,y=115)


        # l2=Label(deletewin,fg="red",text="No Such Record Found",font=("Helvetica",10)).place(x=6,y=115)        

    finally:
        deletewin.after(3000,lambda:deletewin.destroy())       
def recdelete():
    global deletewin
    deletewin=Toplevel(root)
    global e
    e=Entry(deletewin,font=("Helvetica",12))
    e.place(x=5,y=40)
    l=Label(deletewin,font=("Helvetica",12),text="Please Enter Roll No",fg="purple").place(x=5,y=10)
    global button
    button=Button(deletewin,text="OK",command=lambda:clickok(),font=("Helvetica",10),
                  bg="lightpink",fg="purple",borderwidth=0).place(x=100,y=150)
    
def yesclk():
    con=sqlite3.connect('studentrecords.db')
    c=con.cursor()
    c.execute("DELETE FROM StudentData")
    newwind.destroy()
    con.commit()
    con.close()
def clearall():
    global newwind
    newwind=Toplevel(root)
    newwind.geometry('200x200')
    yesbtn=Button(newwind,font=("Helvetica",12),text="Yes",borderwidth=0,bg="lightpink",
                  fg="purple",command=yesclk).place(x=7,y=160)
    nobtn=Button(newwind,font=("Helvetica",12),text="No",borderwidth=0,bg="lightpink",
                 fg="purple",command=lambda:newwind.destroy()).place(x=160,y=160)
    label1=Label(newwind,font=("Arial",15),text="Are You Sure?",fg="purple").place(x=15,y=25)

def clicksubmit():
    print("Called Function")
    con=sqlite3.connect('studentrecords.db')
    c=con.cursor()

    studentname=name.get()
    rollnum=rollno.get()
    math_marks=maths.get()
    phy_marks=physics.get()
    chem_marks=chemistry.get()
    gender=""
    gen=var.get()
    if(gen==1):
        gender+="Male"
    else:
        gender+="Female"    
    c.execute("""INSERT INTO StudentData(Name,Roll,Gender,Maths,Physics,Chemistry) VALUES(?,?,?,?,?,?)""",
              (studentname,rollnum,gender,math_marks,phy_marks,chem_marks))
    rows=c.execute("SELECT * from StudentData")
    print(type(rows))
    for row in rows:
        print(type(row))
        print(row)
        # print("Unable To Enter")

    con.commit()
    name.delete(0,END)
    rollno.delete(0,END)
    maths.delete(0,END)
    physics.delete(0,END)
    chemistry.delete(0,END)
root=Tk()
root.geometry('1000x500')
#root.iconbitmap('ER.ico')
root.title('Exam Records')
var=IntVar()
global con
con=sqlite3.connect('studentrecords.db')
c=con.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS StudentData(Name TEXT,Roll NUMBER,Gender TEXT,\
								Maths NUMBER,Physics NUMBER,Chemistry NUMBER)""")
# Creating Labels
header=Label(root,font=("Arial",15),fg="purple",text="Exam Records").place(x=210,y=30)
name_label=Label(root,font=("Helvetica",12),fg="purple",text="Name").place(x=69,y=120)
gender=Label(root,font=("Helvetica",12),fg="purple",text="Gender").place(x=69,y=164)
roll=Label(root,font=("Helvetica",12),fg="purple",text="Roll Number").place(x=69,y=208)
math_sub=Label(root,font=("Helvetica",12),fg="purple",text="Mathematics").place(x=69,y=250)
phy_sub=Label(root,font=("Helvetica",12),fg="purple",text="Physics").place(x=69,y=290)
chem_sub=Label(root,font=("Helvetica",12),text="Chemistry",fg="purple").place(x=69,y=330)

# Creating Entry Boxes
global name,rbutton1,rbutton2,rollno,maths,physics,chemistry
name=Entry(root,font=("Helvetica",12),width=27,bg="lightblue")
rbutton1=Radiobutton(root,font=("Helvetica",12),fg="red",variable=var,value=1,text="Male")
rbutton2=Radiobutton(root,font=("Helvetica",12),fg="green",variable=var,value=2,text="Female")
rollno=Entry(root,font=("Helvetica",12),width=27,bg="lightblue")
maths=Entry(root,font=("Helvetica",12),width=27,bg="lightblue")
physics=Entry(root,font=("Helvetica",12),width=27,bg="lightblue")
chemistry=Entry(root,font=("Helvetica",12),width=27,bg="lightblue")
# Placing Widgets
name.place(x=170,y=122)
rbutton1.place(x=170,y=164)
rbutton2.place(x=250,y=164)
rollno.place(x=170,y=207)
maths.place(x=170,y=249)
physics.place(x=170,y=289)
chemistry.place(x=170,y=329)
# Create a Submit Button , Delete Record , Clear Data Base
submit=Button(root,font=("Arial",15),fg="white",bg="purple",text="Submit",borderwidth=0,
              command=lambda:clicksubmit()).place(x=242,y=369)
con.commit()
con.close()
delete=Button(root,font=("Helvetica",12),bg="green",fg="white",text="Delete A Record",
              borderwidth=0,command=recdelete).place(x=220,y=410)
frame=Frame(root,bg="lightpink",width=500,height=500).place(x=500,y=0)
clearEntry=Button(root,font=("Helvetica",12),text="Clear Database",bg="red",fg="white",
                  borderwidth=0,command=clearall).place(x=223,y=450)
# Frame Buttons
def mathres():

    print("Inside Math")
    newwind=Toplevel(root)
    lab_header1=Label(newwind,text="Name",font=("Helvetica",10),fg="purple",bg="lightpink").place(x=2,y=0)
    lab_header2=Label(newwind,text="Roll Number",font=("Helvetica",10),fg="purple",bg="lightpink").place(x=152,y=0)
    lab_header3=Label(newwind,text="Marks Obtained",font=("Helvetica",10),fg="purple",bg="lightpink").place(x=302,y=0)
    newwind.geometry('400x400')
    con=sqlite3.connect('studentrecords.db')
    c=con.cursor()
    rows=c.execute("SELECT Name,Roll,Maths FROM StudentData ORDER BY Maths desc")
    x1=2 
    y1=30
    for row in rows:
        s_name=row[0]
        roll=row[1]
        math=row[2]
        lab1=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=s_name).place(x=x1,y=y1)
        lab2=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=str(roll)).place(x=x1+150,y=y1)
        lab3=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=str(math)).place(x=x1+300,y=y1)
        y1+=30

def chemres():
    print("Inside Chem")
    newwind=Toplevel(root)
    lab_header1=Label(newwind,text="Name",font=("Helvetica",10),fg="purple",
                      bg="lightpink").place(x=2,y=0)
    lab_header2=Label(newwind,text="Roll Number",font=("Helvetica",10),fg="purple",
                      bg="lightpink").place(x=152,y=0)
    lab_header3=Label(newwind,text="Marks Obtained",font=("Helvetica",10),fg="purple",
                      bg="lightpink").place(x=302,y=0)
    newwind.geometry('400x400')
    con=sqlite3.connect('studentrecords.db')
    c=con.cursor()
    rows=c.execute("SELECT Name,Roll,Chemistry FROM StudentData ORDER BY Chemistry desc")
    x1=2 
    y1=30
    for row in rows:
        s_name=row[0]
        roll=row[1]
        math=row[2]
        lab1=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=s_name).place(x=x1,y=y1)
        lab2=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=str(roll)).place(x=x1+150,y=y1)
        lab3=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=str(math)).place(x=x1+300,y=y1)
        y1+=30
 
def phyres():
    print("Inside Physics")
    newwind=Toplevel(root)
    lab_header1=Label(newwind,text="Name",font=("Helvetica",10),
                      fg="purple",bg="lightpink").place(x=2,y=0)
    lab_header2=Label(newwind,text="Roll Number",font=("Helvetica",10),
                      fg="purple",bg="lightpink").place(x=152,y=0)
    lab_header3=Label(newwind,text="Marks Obtained",font=("Helvetica",10),
                      fg="purple",bg="lightpink").place(x=302,y=0)
    newwind.geometry('400x400')
    con=sqlite3.connect('studentrecords.db')
    c=con.cursor()
    rows=c.execute("SELECT Name,Roll,Physics FROM StudentData ORDER BY Physics desc")
    x1=2 
    y1=30
    for row in rows:
        s_name=row[0]
        roll=row[1]
        math=row[2]
        lab1=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=s_name).place(x=x1,y=y1)
        lab2=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=str(roll)).place(x=x1+150,y=y1)
        lab3=Label(newwind,font=("Helvetica",10),fg="purple",bg="lightpink",
                   highlightcolor="purple",text=str(math)).place(x=x1+300,y=y1)
        y1+=30

button1=Button(frame,text="Display Maths Results",bg="purple",fg="white",font=("Helvetica",15),
               command=lambda:mathres(),borderwidth=0).place(x=500,y=50)
button2=Button(frame,text="Display Physics Results",bg="purple",fg="white",font=("Helvetica",15),
               command=phyres,borderwidth=0).place(x=500,y=95)
button3=Button(frame,text="Display Chemistry Results",bg="purple",fg="white",font=("Helvetica",15),
               borderwidth=0,command=chemres).place(x=500,y=140)

root.mainloop()
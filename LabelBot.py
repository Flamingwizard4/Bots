#!/usr/bin/python

##LabelBot - GUI for rapid dataset creation
#
# pipeline from SearchBot
# add video functionality with pause/clip buttons in vidFrame
# add value display for selection only labels
# fix cut-off labelframes
# add image examples w/ categories/slideshow in lframe
# add hyperlink section
# image progress status bar
# finish parseLbls
#   
# save images as dictionaries with imgs as numpy arrays, BB coords, and labels
# when displaying images check for img_bounded.csv in directory?
# 
# save symptoms as multiple one-hot vectors with values of either 0 or 1 in img_labeled.csv
# add dual status bar with real-time directions on right (e.g. click and drag to select bounding box, right click in box to delete) and imagecount progess on left
# add save and exit button in between last/next image buttons instead of turning next to exit
# add dialog box for optional deleting of old images in directory
##
import os, re, math
import pickle
from tkinter import *
from PIL import ImageTk, Image, ImageDraw
from time import sleep
import numpy as np


'''METHODS:'''
'''add working __refreshImg/individual BBs to these:'''
#go to next image    
def nextImg():
    global imgCanvas
    global nextImgButt
    global backImgButt
    global imgcount
    global images
    imgcount += 1
    imgCanvas.grid_forget()    
    imgCanvas = Canvas(imgFrame, width=512, height=512)
    imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
    imgCanvas.grid(row=0, column=0, columnspan=2)
    nextImgButt.grid_forget()
    if imgcount == len(lims) - 1:
        nextImgButt = Button(imgFrame, text="Exit", command=m.quit, padx=40, pady=15)
    else:
        nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
    nextImgButt.grid(row=1, column=1, sticky="nsew")
    backImgButt.grid_forget()
    backImgButt = Button(imgFrame, text="Last Image", command=backImg, padx=20, pady=15)
    backImgButt.grid(row=1, column=0, sticky="nsew")
    imgStatus.config(text="Image %d of %d"%(imgcount+1, len(lims)))
    __refreshImg()
#go to previous image    
def backImg():
    global imgCanvas
    global nextImgButt
    global backImgButt
    global imgcount
    global images
    imgcount -= 1
    imgCanvas.grid_forget()    
    imgCanvas = Canvas(imgFrame, width=512, height=512)
    imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
    imgCanvas.grid(row=0, column=0, columnspan=2)
    if imgcount == 0:
        backImgButt.config(state=DISABLED)
    else:
        backImgButt.config(state=NORMAL)
    backImgButt.grid(row=1, column=0, sticky="nsew")
    nextImgButt.grid_forget()
    nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
    nextImgButt.grid(row=1, column=1, sticky="nsew")
    imgStatus.config(text="Image %d of %d"%(imgcount+1, len(lims)))
    __refreshImg()
#save image with labels and values in pickled dictionary
def __saveImg(imarray, imcount):
    pass
           
#add BB button com
def add_bb():
    imgCanvas.bind('<Button-1>', __draw_bb)
    imgCanvas.bind('<ButtonRelease-1>', __save_bb)
    imgCanvas.config(cursor='cross')
    remCowButt.config(state=DISABLED)
    helpStatus.config(text="Click and drag to draw a bounding box around an individual:")
#draw BB in real-time    
def __draw_bb(event):
    global loc1
    imgCanvas.bind('<Motion>', __draw_rec)
    loc1 = (event.x, event.y)
    print("Coords 1: ")
    print(loc1)  
#draw BB rectangle
def __draw_rec(event):
    global loc1
    global images
    global imgcount
    global boxes
    __refreshImg()
    csrLoc = (event.x, event.y)
    coords = [loc1[0], loc1[1], csrLoc[0], csrLoc[1]]
    imgCanvas.create_rectangle(coords, outline="red", fill="", width=3)
#save BBs - NOTE: this is completely wrong for now
def __save_bb(event):
    global loc1
    global loc2
    imgCanvas.unbind('<Motion>')
    imgCanvas.unbind('<Button-1>')
    imgCanvas.unbind('<ButtonRelease-1>')
    loc2 = (event.x, event.y)
    print("Coords 2: ")
    print(loc2)
    imgdict[imgcount]['box'].append([loc1[0], loc1[1], loc2[0], loc2[1]])
    imgCanvas.config(cursor='')
    remCowButt.config(state=NORMAL)
    helpStatus.config(text="Bounding box saved.")
#remove BB button com
def rem_bb():
    imgCanvas.bind('<Button-1>', __del_bb)
    imgCanvas.config(cursor="pirate")
    addCowButt.config(state=DISABLED)
    helpStatus.config(text="Click near the center of the bounding box you want to delete:")
#delete BB
def __del_bb(event):
    imgCanvas.unbind('<Button-1>')
    selX = event.x
    selY = event.y
    boxcount, cDist, cBox = 0, 0, 0
    for box in imgdict[imgcount]['box']:
        x = box[0] + (box[2]/2)
        y = box[1] + (box[3]/2)
        dist = math.sqrt((selX-x)**2 + (selY-y)**2)
        if dist < cDist:
            cBox = boxcount
            cDist = dist
        boxcount += 1
    del imgdict[imgcount]['box'][cBox] #delete bounding box
    __refreshImg()
    imgCanvas.config(cursor="")
    addCowButt.config(state=NORMAL)
    helpStatus.config(text="Bounding box deleted.")
#update BBs
def __refreshImg():
    imgCanvas.delete('all')
    imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
    for loc in imgdict[imgcount]['box']:
        imgCanvas.create_rectangle(loc, outline="red", fill="", width=3)
#select individual BB
def sel_bb():
    pass
#parse labels.txt - NOTE: user needs to have spaces after "LABEL:" & "INFO:"
#add & functionality
#add EXAMPLES:
def __parseLbls(path):
    labels = [] #list of label dictionaries
    textlines = [] #list of lines in label
    linesleft = [] #list of lines left to parse
    with open(path, "r") as label_doc:
        for line in label_doc:
            textlines.append(line)
    textlines.append(None)#end loop
    lflag = True #start loop
    while lflag:
        lflag=False #start fresh for each symptom
        dflag=False #description flag
        eflag=False
        lcount=0
        if linesleft:
            textlines = linesleft
        name=""
        desc=""
        exam=""   
        opt=None #potential options for symptom/label
        if len(textlines) > 0:
            for line in textlines:
                if line is None:
                    lflag = False
                    ldict = {"name":re.sub("\n", "", name), "desc":re.sub("\n", "", desc), "exam":re.sub("\n", "", exam)}
                    if opt:
                        ldict['opt'] = opt
                    labels.append(ldict)
                    break
                elif "LABEL:" in line:
                    if lflag: #new symptom reached
                        ldict = {"name":re.sub("\n", "", name), "desc":re.sub("\n", "", desc), "exam":re.sub("\n", "", exam)}
                        if opt:
                            ldict['opt'] = opt
                        labels.append(ldict)
                        linesleft = textlines[lcount:]
                        break #starts from where symptom left off
                    else:
                        lflag = True
                        name = line.split(" ")[1:]
                        name = " ".join(name)
                        if "(" in line:
                            opt = re.sub("\n", "", line.split("(")[1][:-2])
                            name = name.split("(")[0][:-1]#hopefully this works
                elif "INFO:" in line:
                    desc = line[5:]#could be [4:]
                elif "EXAM:" in line:
                    exam = line[5:]
                else:
                    if dflag:
                        desc += line
                    elif eflag:
                        exam += line
                lcount += 1
    #print(labels)
    return labels            
#clear label frames    
def __clrLbls():
    for widget in lblFrame.winfo_children(): #lFrames
            widget.grid_forget()
            for wid in widget.winfo_children(): #Label sections
                if wid.winfo_class() == "Scale":
                    wid.destroy() #destroys opt sliders
                elif wid.winfo_class() == "Labelframe":
                    wid.grid_forget()
                    for w in wid.winfo_children():
                        w.destroy() #destroys opt buttons+
                elif wid.winfo_class() == "Label" and wid['text'] == "":
                    wid.destroy() #destroys padding labels
#create/redraw label frames
def __addLbls(lbls):
    #global lFrames
    for l in range(len(lbls)):
        if len(lFrames) != len(lbls):#create lFrames
            lFrames[l], sVars[l], vVars[l], nVars[l] = __createLbl(l)
        else:#redraw lFrames
            for widget in lFrames[l].winfo_children():
                if (widget.winfo_class() == "Label") and (widget['text'] == "/\\"): #change eLabel to extend
                    widget.unbind('<Button-1>')
                    widget.config(text="\/")
                    widget.bind('<Button-1>', lambda event, x=l: extLbl(x))
                    break
        lFrames[l].grid(row=l, column=0)    
#create label frame        
def __createLbl(n):
    name = lbls[n]['name']
    desc = lbls[n]['desc']
    opt = lbls[n]['opt'] if ('opt' in lbls[n]) else None
    lFrame = Frame(lblFrame, pady=10)
    lFrame.grid(row=1, column=0) #is this line necessary with line 279?
    lFrame.grid_columnconfigure(0, weight=1)
    sVar = IntVar()#selection variable
    vVar = DoubleVar()#value variable for options
    nVar = StringVar()#dynamic name variable
    nVar.set(name)
    #selection button
    s = Radiobutton(lFrame, variable=sVar, value=1, command=lambda: selLbl(n), textvariable=nVar)
    s.grid(row=0, column=0)
    #reset button for clearing selection/value
    resButt = Button(lFrame, text="Reset", command=lambda: reset(n), anchor=E, padx=1)
    resButt.grid(row=0, column=1)
    #extend/retract event label
    eLabel = Label(lFrame, text = "\/", pady=5)
    eLabel.bind('<Button-1>', lambda event: extLbl(n))
    eLabel.grid(row=1, column=0, columnspan=2, sticky=W+E)
    return lFrame, sVar, vVar, nVar
#reset variables and retract    
def reset(n):
    name = lbls[n]['name']
    sVars[n].set(0)
    vVars[n].set(0)
    nVars[n].set(name)
    retract()
    helpStatus.config(text="Reset %s variables."%name)
#create option bar
def __createOp(n, opFrame, ops, step, buttonsWidth):
    #global lFrames
    optButt={}
    optlist = ops.split(",")
    for i in range(len(optlist)): #stripping options
        newOpt = optlist[i].strip()
        optlist[i] = newOpt            
    for o in range(len(optlist)): #creating buttons
        #print(optlist[o][:-4])
        val = float(optlist[o][-3:]) #format is "LABEL: FULL NAME (OPTION1:VAL1&OPTION2.1:VAL2.1,OPTION2.2:VAL2.2)" with values ranging from 0.0 to 1.0
        optButt[o] = Button(opFrame, text=optlist[o][:-4], command=lambda x=o, v=val: selOpt(optButt, optlist[x], n, v, step), padx=1, pady=5)
        if step != 0: #disables additional buttons
            optButt[o].config(state=DISABLED)
        if len(optlist) == 1:
            optButt[o].grid(row=step, column=o, columnspan = buttonsWidth, sticky="nsew")
        else:
            optButt[o].grid(row=step, column=o, sticky="nsew")
        if val <= vVars[n].get(): #remember option selections
            optButt[o].config(relief=SUNKEN)
#extend label frame to show additional options, description, and examples
def extend(n):
    #global lFrames
    name = lbls[n]['name']
    desc = lbls[n]['desc']
    exam = lbls[n]['exam']
    opt = lbls[n]['opt'] if ('opt' in lbls[n]) else None
    #global lFrames
    for f in range(len(lFrames)):
        lFrames[f].grid_forget() #could be more specific
    lFrames[n].grid(row=0, column=0)
    for widget in lFrames[n].winfo_children():
        if widget['text'] == "\/": #change eLabel to retract
            widget.unbind('<Button-1>')
            widget.config(text="/\\")
            widget.bind('<Button-1>', lambda event: retract())
            break
    if opt:
        oFrame = LabelFrame(lFrames[n], text="Options")
        oFrame.grid(row=2, column=0, sticky="nsew", columnspan=2)
        if opt == "$":
            for i in range(2):
                oFrame.grid_columnconfigure(i, weight=1)
            slider = Scale(oFrame, from_=0, to=1, orient=HORIZONTAL, tickinterval=.5, variable=vVars[n], resolution=0.01, command=lambda event: selSld(n))
            slider.grid(row=2, column=0, columnspan=2, sticky=W+E)
        else: #button options
            if "&" in opt:
                bw = 0
                opts = opt.split("&") #list for hierarchical optButt dictionaries
                #print(opts)
                for op in opts: #find button width
                    if bw < len(op.split(",")):
                        bw = len(op.split(","))       
                for c in range(bw):
                    lFrames[n].grid_columnconfigure(c, weight=1)  
                    oFrame.grid_columnconfigure(c, weight=1)
                for o in range(len(opts)): #create hierachical option buttons
                    __createOp(n, oFrame, opts[o], o, bw)
                  
            else:
                for c in range(len(opt.split(","))):
                    lFrames[n].grid_columnconfigure(c, weight=1)  
                    oFrame.grid_columnconfigure(c, weight=1)
                __createOp(n, oFrame, opt, 0, len(opt.split(",")))
        crow=3
    else:
        crow=2
    pLabel = Label(lFrames[n], pady=1) #padding label
    pLabel.grid(row=crow, column=0)    
    crow+=1
    dFrame = LabelFrame(lFrames[n], text="Description") #description frame
    dFrame.grid(row=crow, column=0, sticky="nsew")
    crow+=1
    dLabel = Label(dFrame, text=desc) 
    dLabel.grid(row=0, column=0, sticky="nsew")
    pLabel2 = Label(lFrames[n], pady=1) #padding label 2
    pLabel2.grid(row=crow, column=0)
    crow+=1
    xFrame = LabelFrame(lFrames[n], text="Examples") #example frame
    xFrame.grid(row=crow, column=0, sticky="nsew")
    crow+=1
    xLabel = Label(xFrame, text=exam)
    xLabel.grid(row=0, column=0, sticky="nsew")    
            
    #add label for text description
    #add panes/frame for example images with option for see more 
    #which if no appropriate dir is found just pulls up a google images search of the symptom   
#retract extended info    
def retract():
    __clrLbls()
    __addLbls(lbls)
    helpStatus.config(text="Labeling Interface.")
    #__printVars()
#select label
def selLbl(n):
    helpStatus.config(text="Selected %s."%lbls[n]['name'])
    extend(n)
#extend label
def extLbl(n):
    helpStatus.config(text="Extended %s."%lbls[n]['name'])
    extend(n)
#mutually exclusive button select   
def selOpt(opDict, op, varNum, value, step):
    for wid in lFrames[varNum].winfo_children():
        if wid.winfo_class() == "Radiobutton":
            wid.select()
        elif wid['text'] == "Options":
            for w in wid.winfo_children():
                if w.grid_info()['row'] == step+1:
                    w.config(state=NORMAL)
                elif w.grid_info()['row'] == step-1:
                    w.config(state=DISABLED)   
    vVars[varNum].set(value)
    nVars[varNum].set(lbls[varNum]['name']+":%.2f"%vVars[varNum].get())#display value in name
    for o in opDict:
        if opDict[o]['text'] != op[:-4]: #assuming ":1.0" or ":.75" format
            opDict[o].config(relief=RAISED)
        else:
            opDict[o].config(relief=SUNKEN)
    helpStatus.config(text="Set value of "+op[:-4]+" to %0.1f"%value)

#slider response
def selSld(n):
    name = lbls[n]['name']
    val = vVars[n].get()
    for wid in lFrames[n].winfo_children():
        if wid.winfo_class() == "Radiobutton":
            wid.select()
    nVars[n].set(name+": %0.2f"%val)
    helpStatus.config(text="Set value of "+name+" to %0.2f"%val)
#print selection/value variables for debug purposes
def __printVars():
    global sVars
    global vVars
    for s in sVars:
        try:
            print("Selection Variable #%d"%s, sVars[s].get())
        except:
            print("Couldn't get sel var %s"%sVars[s]) 
    for v in vVars:
        try:
            print("Value Variable #%d"%v, vVars[v].get())
        except:
            print("Couldn't get val var %s"%vVars[v])
    
#switch between bounding box and symptom labels mode
def selMode(mode):
    if mode == "BB":
        lblButt.config(relief=RAISED)
        bbButt.config(relief=SUNKEN)
        __clrLbls()
        addCowButt.grid(row=0, column=0, sticky="nsew", pady=(180, 30))
        remCowButt.grid(row=1, column=0, sticky="nsew", pady=(30, 180))
        helpStatus.config(text="Bounding Interface.")
    elif mode == "SL":
        bbButt.config(relief=RAISED)
        lblButt.config(relief=SUNKEN)
        __clrLbls()
        __addLbls(lbls)
        helpStatus.config(text="Labeling Interface.")

#open window in top left of screen
def __topleft_window(width=750, height=630):
    # get screen width and height
    screen_width = m.winfo_screenwidth()
    screen_height = m.winfo_screenheight()

    '''#centering x and y coordinates
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    '''
    m.geometry('%dx%d+%d+%d' % (width, height, 0, 0))
            
"""INITIAL SETUP:"""
m = Tk() #main window
m.title("LabelBot - Dataset Creation GUI")
#m.iconbitmap(logo.ico)
cdir = os.getcwd()
idir = os.path.join(cdir, "labels", "unlabeled_images")#should I keep unlabeled_images??
lblinfopath = os.path.join(cdir, "labels", "labels.txt")   
lims = os.listdir(idir) #images files to label
imgdict = {} #Attributes: img, box, lbl, val
images = [] #temporary storage for Tkinter images
imgcount = 0
for im in lims:
    imgdict[imgcount] = {"img":np.asarray(Image.open(os.path.join(idir, im))), "box":[]}
    images.append(ImageTk.PhotoImage(Image.open(os.path.join(idir, im)).resize((512,512)))) #should Image.fromarray(imgdict[imgcount]['img']).resize((512, 512)) be used instead of opening?
    imgcount += 1
imgcount = 0
loc1, loc2 = (0, 0), (0, 0) #storage containers for cursor locations
print("Current Directory: %s"%cdir)
#print("There are %d images to label."%len(images))

modeButts = LabelFrame(m, text="Label Mode", bd=0, labelanchor=N) #mode selector top bar
modeButts.grid(row=0, column=0, columnspan=2, sticky="nsew")
modeButts.grid_columnconfigure(0, weight=1)
modeButts.grid_columnconfigure(1, weight=1)

bbButt = Button(modeButts, text="Bounding Boxes", command=lambda : selMode("BB"))
bbButt.grid(row=0, column=0, sticky="nsew")
lblButt = Button(modeButts, text="Symptom Labels", command=lambda : selMode("SL"))
lblButt.grid(row=0, column=1, sticky="nsew")

#image/label frames
imgFrame = Frame(m, padx=2)
imgFrame.grid(row=1, column=0)
lblFrame = LabelFrame(m, padx=2)
lblFrame.grid(row=1, column=1, sticky="nsew")
m.grid_columnconfigure(1, weight=1)
lblFrame.grid_columnconfigure(0, weight=1)

imgCanvas = Canvas(imgFrame, width=512, height=512)
imgCanvas.create_image(0, 0, image=images[0], anchor=NW)
imgCanvas.grid(row=0, column=0, columnspan=2)

backImgButt = Button(imgFrame, text="Last Image", state=DISABLED, padx=20, pady=15)
backImgButt.grid(row=1, column=0, sticky="nsew")
nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
nextImgButt.grid(row=1, column=1, sticky="nsew")

statusBar = LabelFrame(m, text="Help") #image progress and directions displayer
statusBar.grid(row=2, column=0, columnspan=2, sticky="nsew")
statusBar.grid_columnconfigure(0, weight=1)
statusBar.grid_columnconfigure(1, weight=1)
helpStatus = Label(statusBar, text="This is where help info goes.", anchor=W, bd=1)
helpStatus.grid(row=0, column=0, sticky="nsew")
imgStatus = Label(statusBar, text="Image 1 of 3.", anchor=E, bd=1)
imgStatus.grid(row=0, column=1, sticky="nsew")

addCowButt = Button(lblFrame, text="Add Box", command=add_bb, padx=20, pady=15)
remCowButt = Button(lblFrame, text="Remove Box", command=rem_bb, padx=20, pady=15)
  
lbls = __parseLbls(lblinfopath) #parsing labels.txt 

lFrames, sVars, vVars, nVars = {}, {}, {}, {} #label frame storage

__topleft_window(750, 630)
m.mainloop()

#example image dictionary entry
'''
{
    "img":nparr,
    "box":coordlist,
    "lbl":lblnames,
    "val: lblvec
}
'''
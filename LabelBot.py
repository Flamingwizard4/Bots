#!/usr/bin/python

##LabelBot - Program for rapid creation of annotated ML datasets
#
# pipeline from SearchBot
#
# save images as dictionaries with imgs as numpy arrays, BB coords, and labels
# when displaying images check for img_bounded.csv in directory?
# 
# symptom tab with list of expandable/selectable symptoms
# save symptoms as multiple one-hot vectors with values of either 0 or 1 in img_labeled.csv
# add dual button header to switch between bounding boxing and symptom labeling
# add dual status bar with real-time directions on right (e.g. click and drag to select bounding box, right click in box to delete) and imagecount progess on left
# add save and exit button in between last/next image buttons
# add dialog box for optional deleting of old images in directory
#
#if symptom has options then expand automatically once selected
##


import os, re, math
from tkinter import *
from PIL import ImageTk, Image, ImageDraw
from time import sleep#, time
from decimal import Decimal

m = Tk() #main window
m.title("LabelBot - Dataset Creation GUI")
#m.iconbitmap(logo.ico)

cdir = os.getcwd()
print("Current Directory: %s"%cdir)
ldir = os.path.join(cdir, "labels", "unlabeled_images")#are these stored as numpy arrays in csv files or as real pictures??
lblinfopath = os.path.join(cdir, "labels", "labels.txt")   
#images to label
lims = os.listdir(ldir)
imgcount = 0
images, boxes = [], [] #changes boxes to dictionary per image with np imgs
for im in lims:
    images.append(ImageTk.PhotoImage(Image.open(os.path.join(ldir, im)).resize((512,512)))) #change to storing images as numpy arrays in dictionaries
#print("There are %d images to label."%len(images))

loc1, loc2 = (0, 0), (0, 0) #storage containers for cursor locations

#opens window in top left of screen
def topleft_window(width=500, height=500):
    # get screen width and height
    screen_width = m.winfo_screenwidth()
    screen_height = m.winfo_screenheight()

    '''#centering x and y coordinates
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    '''
    m.geometry('%dx%d+%d+%d' % (width, height, 0, 0))

#parses labels.txt - needs to have spaces after "LABEL:" & "INFO:" 
def parseLabels(path):
    symptoms = [] #list of symptom dictionaries
    textlines = [] #list of lines in labels.txt
    linesleft = [] #list of lines left to parse
    with open(path, "r") as label_doc:
        for line in label_doc:
            textlines.append(line)
    textlines.append(None)
    sflag = True #just to start loop
    while sflag:
        sflag=False #start fresh for each symptom
        lcount=0
        if linesleft:
            textlines = linesleft
        name=""
        desc=""   
        opt=None #potential options for symptom/label
        if len(textlines) > 0:
            for line in textlines:
                if line is None:
                    sflag = False
                    sdict = {"name":re.sub("\n", "", name), "desc":re.sub("\n", "", desc)}
                    if opt:
                        sdict['opt'] = opt
                    symptoms.append(sdict)
                    break
                elif "LABEL:" in line:
                    if sflag: #new symptom reached
                        sdict = {"name":re.sub("\n", "", name), "desc":re.sub("\n", "", desc)}
                        if opt:
                            sdict['opt'] = opt
                        symptoms.append(sdict)
                        linesleft = textlines[lcount:]
                        break
                    else:
                        sflag = True
                        name = line.split(" ")[1:]
                        name = " ".join(name)
                        ###re.sub \n
                        #print(name)
                        if "(" in line:
                            opt = re.sub("\n", "", line.split("(")[1][:-2])
                            name = name.split("(")[0][:-1] #hopefully this works
                        lcount += 1
                elif "INFO:" in line:
                    desc = line[5:]#could be [4:]
                    lcount += 1
                else:
                    desc += line
                    lcount += 1
    return symptoms

'''add working refreshImg to these:'''
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
        nextImgButt = Button(imgFrame, text="Exit", command=m.quit, padx=20, pady=15)
    else:
        nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
    nextImgButt.grid(row=1, column=1)
    backImgButt.grid_forget()
    backImgButt = Button(imgFrame, text="Last Image", command=backImg, padx=20, pady=15)
    backImgButt.grid(row=1, column=0)
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
    backImgButt.grid_forget()
    if imgcount == 0:
        backImgButt = Button(imgFrame, text="Last Image", command=backImg, padx=20, pady=15, state=DISABLED)
    else:
        backImgButt = Button(imgFrame, text="Last Image", command=backImg, padx=20, pady=15)
    backImgButt.grid(row=1, column=0)
    nextImgButt.grid_forget()
    nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
    nextImgButt.grid(row=1, column=1)
    
    #addCowButt = Button(imgFrame, text="Add Cow", command=addCow, padx=20, pady=15)
    #addCowButt.grid(row=1, column=1) 
            
#add BB button com
def add_bb():
    imgCanvas.bind('<Button-1>', __draw_bb)
    imgCanvas.bind('<ButtonRelease-1>', __save_bb)
    #disable removeCow button
#draw BB in real-time    
def __draw_bb(event):
    global loc1
    imgCanvas.bind('<Motion>', __draw_rec)
    loc1 = (event.x, event.y)
    print("Coords 1: ")
    print(loc1)  
#draws BB rectangle
def __draw_rec(event):
    global loc1
    global images
    global imgcount
    global boxes
    refreshImg()
    csrLoc = (event.x, event.y)
    coords = [loc1[0], loc1[1], csrLoc[0], csrLoc[1]]
    imgCanvas.create_rectangle(coords, outline="red", fill="", width=3)
#saves BBs  
def __save_bb(event):
    global loc1
    global loc2
    global boxes
    imgCanvas.unbind('<Motion>')
    imgCanvas.unbind('<Button-1>')
    imgCanvas.unbind('<ButtonRelease-1>')
    loc2 = (event.x, event.y)
    print("Coords 2: ")
    print(loc2)
    boxes.append([loc1[0], loc1[1], loc2[0], loc2[1]]) #change to dictionary
    #reenable removeCow button
#remove BB button com
def rem_bb():
    imgCanvas.bind('<Button-1>', __sel_bb)
    #disable addCow button
#select BB to remove
def __sel_bb(event):
    global boxes
    imgCanvas.unbind('<Button-1>')
    selX = event.x
    selY = event.y
    boxcount, cDist, cBox = 0, 0, 0
    for box in boxes:
        x = box[0] + (box[2]/2)
        y = box[1] + (box[3]/2)
        dist = math.sqrt((selX-x)**2 + (selY-y)**2)
        if dist < cDist:
            cBox = boxcount
            cDist = dist
        boxcount += 1
    print(cBox)
    del boxes[cBox]
    refreshImg()
    #reenable addCow button
#updates BBs
def refreshImg():
    imgCanvas.delete('all')
    imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
    if boxes:
        for loc in boxes:
            imgCanvas.create_rectangle(loc, outline="red", fill="", width=3)
            
#adds/redraws lFrames
def addLBLs(lbls):
    global lFrames
    for l in range(len(lbls)):
        if len(lFrames) != len(lbls): 
            if 'opt' in lbls[l]:  
                lFrames[l], sVars[l], vVars[l] = __addSymptom(lbls[l]['name'], lbls[l]['desc'], lbls[l]['opt'])
            else:
                lFrames[l], sVars[l], vVars[l] = __addSymptom(lbls[l]['name'], lbls[l]['desc'])
        else:
            for widget in lFrames[l].winfo_children():
                if (widget.winfo_class() == "Label") and (widget['text'] == "/\\"):
                    widget.unbind('<Button-1>')
                    widget.config(text="\/")
                    widget.bind('<Button-1>', lambda event, x=l: extend(lbls[x]['name'], lbls[x]['desc'], lbls[x]['opt']) if 'opt' in lbls[x] else extend(lbls[x]['name'], lbls[x]['desc']))
                    break
        lFrames[l].grid(row=l, column=0)    
#draws symptom frame        
def __addSymptom(name, desc, options=None):
    lFrame = Frame(lblFrame, pady=10)
    lFrame.grid(row=1, column=0) #is this line necessary with line 279?
    sVar = IntVar()#variable for radiobutton selection
    vVar = DoubleVar()#value variable for options
    #contents
    s = Radiobutton(lFrame, text=name, variable=sVar) #check for whether options are present and if so make extend automatic
    s.grid(row=0, column=0)
    #reset button for clearing selection/value
    sReset = Button(lFrame, text="Reset", command=lambda: reset(sVar, vVar), anchor=E)
    sReset.grid(row=0, column=1)
    #extend/retract label
    eLabel = Label(lFrame, text = "\/", padx=5)
    eLabel.bind('<Button-1>', lambda event: extend(name, desc, options) if options else extend(name, desc))
    eLabel.grid(row=1, column=0, columnspan=2, sticky=W+E)
    return lFrame, sVar, vVar
#undo selection/value and retract    
def reset(svar, vvar):
    svar.set(0)
    vvar.set(0)
    retract() 
#extends label to show additional info, examples, and options    
def extend(name, info, opt=None):
    global lFrames
    for f in range(len(lFrames)):
        for wid in lFrames[f].winfo_children():
            if wid['text'] == name:
                cVar = f #current lFrame num
        lFrames[f].grid_forget()#should I not forget the current lFrame??
    lFrames[cVar].grid(row=0, column=0)
    for widget in lFrames[cVar].winfo_children():
        if widget.winfo_class() == "Label" and widget['text'] == "\/":
            widget.unbind('<Button-1>')
            widget.config(text="/\\")
            widget.bind('<Button-1>', lambda event: retract())
            break
    if opt:
        if opt == "$":
            #slider code
            pass
        else: #option buttons
            optButts={}
            optlist = opt.split(",")
            for n in range(len(optlist)):
                newOpt = optlist[n].strip()
                optlist[n] = newOpt              
            for o in range(len(optlist)):
                val = float(optlist[o][-3:])
                optButts[o] = Button(lFrames[cVar], text=optlist[o][:-4], command=lambda x=o, v=val: selOpt(optButts, optlist[x], vVars[cVar], v), padx=10, pady=5)#why are button commands not reactive??
                optButts[o].grid(row=2, column=o)
                if val == vVars[cVar].get():
                    optButts[o].config(relief=SUNKEN)
    #add label for text description
    #add panes/frame for example images with option for see more 
    #which if no appropriate dir is found just pulls up a google images search of the symptom   
#retracts extended info    
def retract():
    #clears symptom Frames
    for frame in lblFrame.winfo_children():
        frame.grid_forget()
        for w in frame.winfo_children():
            if w.winfo_class() == "Button" and w['text'] != "Reset":
                w.destroy() #destroys option buttons
    #redraws symptom Frames
    addLBLs(lbls)
#mutually exclusive button select    
def selOpt(optDict, option, var, value):
    var.set(value)
    for b in optDict:
        if optDict[b]['text'] != option[:-4]:
            optDict[b].config(relief=RAISED)
        else:
            optDict[b].config(relief=SUNKEN)

#switch between bounding box and symptom labels mode
def selMode(mode):
    if mode == "BB":
        lblButt.config(relief=RAISED)
        bbButt.config(relief=SUNKEN)
        for frame in lblFrame.winfo_children():
            frame.grid_forget()
            for w in frame.winfo_children():
                if w.winfo_class() == "Button" and w['text'] != "Reset":
                    w.destroy() #destroys option buttons
        addCowButt.grid(row=0, column=0, sticky="nsew")
        remCowButt.grid(row=1, column=0, sticky="nsew")
    elif mode == "SL":
        bbButt.config(relief=RAISED)
        lblButt.config(relief=SUNKEN)
        for frame in lblFrame.winfo_children():
            frame.grid_forget()
        addLBLs(lbls)
        
"""WIDGETS:"""

labelButts = Frame(m)
labelButts.grid(row=0, column=0, columnspan=2, sticky=N+S+E+W)
labelButts.grid_columnconfigure(0, weight=1)
labelButts.grid_columnconfigure(1, weight=1)

bbButt = Button(labelButts, text="Bounding Boxes", command=lambda : selMode("BB"))
bbButt.grid(row=0, column=0, sticky="nsew")
lblButt = Button(labelButts, text="Symptom Labels", command=lambda : selMode("SL"))
lblButt.grid(row=0, column=1, sticky="nsew")

#image/label frames
imgFrame = LabelFrame(m, text="Image Frame", padx=2, pady=2)
imgFrame.grid(row=1, column=0)
lblFrame = LabelFrame(m, text="Label Frame", padx=2, pady=2)
lblFrame.grid(row=1, column=1, sticky="nsew")
m.grid_columnconfigure(1, weight=1)
lblFrame.grid_columnconfigure(0, weight=1)

imgCanvas = Canvas(imgFrame, width=512, height=512)
imgCanvas.create_image(0, 0, image=images[0], anchor=NW)
imgCanvas.grid(row=0, column=0, columnspan=2)

backImgButt = Button(imgFrame, text="Last Image", state=DISABLED, padx=20, pady=15)
backImgButt.grid(row=1, column=0)
nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
nextImgButt.grid(row=1, column=1)

addCowButt = Button(lblFrame, text="Add Box", command=add_bb, padx=20, pady=15)
remCowButt = Button(lblFrame, text="Remove Box", command=rem_bb, padx=20, pady=15)


#parsing labels.txt   
lbls = parseLabels(lblinfopath)
#print(lbls)

#populating label frame with parsed lbls
#label frame storage
lFrames, sVars, vVars = {}, {}, {}

topleft_window(700, 620)
m.mainloop()
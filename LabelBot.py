#!/usr/bin/python

##LabelBot - GUI for rapid dataset creation
#
# pipeline from SearchBot
#
# add video functionality with pause/clip buttons in vidFrame
# add image examples w/ categories/slideshow in lframe
# add hyperlink section
# when displaying images check for pickle in directory?
# add dialog box for optional deleting of old images in directory
##
import os, re, math
import pickle
from tkinter import *
from PIL import ImageTk, Image, ImageDraw
from time import sleep
import numpy as np
import tkinter.scrolledtext as tkst

'''Image Buttons:'''
#go to next image    
def nextImg(indMode=False):
    global imgCanvas
    global imgcount
    global indcount
    if indMode:
        __clrVars()
        indcount += 1
        __clrLbls()
        __addLbls()
        imgCanvas.grid_forget()    
        imgCanvas.create_image(0, 0, image=inds[imgcount][indcount], anchor=NW)
        imgCanvas.grid(row=0, column=0, columnspan=2)
        if len(inds[imgcount]) != 1:
            nextButt.config(text="Next Individual")
            nextButt.config(command=lambda: nextImg(True))
        elif len(images) == imgcount:
            nextButt.config(text="Save & Exit")
            nextButt.config(command=pklAll)
        if indcount == len(inds[imgcount])-1:
            nextButt.config(text="Next Image")
            nextButt.config(command=nextImg)
        prevButt.config(command=lambda: backImg(True))
        prevButt.config(state=NORMAL)
        prevButt.config(text="Previous Individual")
        helpStatus.config(text="Labeling Individual %d of %d."%(indcount+1, len(inds[imgcount])))
    else: #image mode
        if sVars:
            __clrVars()
            indcount = 0
        imgcount += 1
        if not inds[imgcount]:
            lblButt.config(state=DISABLED)
            lblIndsButt.config(state=DISABLED)
        else:
            lblButt.config(state=NORMAL)
            lblIndsButt.config(state=NORMAL)
        imgCanvas.grid_forget()    
        imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
        imgCanvas.grid(row=0, column=0, columnspan=2)
        if imgcount == len(images) - 1:
            nextButt.config(text="Save & Exit")
            nextButt.config(command=pklAll)
        else:
            nextButt.config(text="Next Image")
            nextButt.config(command=nextImg)
        prevButt.config(state=NORMAL)
        prevButt.config(command=backImg)
        prevButt.config(text="Previous Image")
        __selMode("BB")
        __refreshImg()
        helpStatus.config(text="Image %d of %d."%(imgcount+1, len(lims)))
#go to previous image    
def backImg(indMode=False):
    global imgCanvas
    global imgcount
    global indcount
    if indMode:
        __clrVars()
        indcount -= 1
        __clrLbls()
        __addLbls()
        imgCanvas.grid_forget()    
        imgCanvas.create_image(0, 0, image=inds[imgcount][indcount], anchor=NW)
        imgCanvas.grid(row=0, column=0, columnspan=2)
        if imgcount == 0:
            prevButt.config(state=DISABLED)
        else:
            prevButt.config(state=NORMAL)
        if indcount != 0:
            prevButt.config(command=lambda: backImg(True))
            prevButt.config(text="Previous Individual")
        else:
            prevButt.config(command = backImg)
            prevButt.config(text="Previous Image")
        nextButt.config(text="Next Individual")
        nextButt.config(command= lambda: nextImg(True))
        helpStatus.config(text="Labeling Individual %d of %d."%(indcount+1, len(inds[imgcount])))
    else: #image mode
        if sVars:
            __clrVars()
            indcount = 0
        imgcount -= 1
        if not inds[imgcount]:
            lblButt.config(state=DISABLED)
            lblIndsButt.config(state=DISABLED)
        else:
            lblButt.config(state=NORMAL)
            lblIndsButt.config(state=NORMAL)
        imgCanvas.grid_forget()    
        imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
        imgCanvas.grid(row=0, column=0, columnspan=2)
        helpStatus.config(text="Image %d of %d."%(imgcount+1, len(lims)))
        if imgcount == 0:
            prevButt.config(state=DISABLED)
        else:
            prevButt.config(state=NORMAL)
        nextButt.config(text="Next Image")
        nextButt.config(command=nextImg)
        prevButt.config(text="Previous Image")
        prevButt.config(command=backImg)
        __selMode("BB")
        __refreshImg()

'''Bounding Boxes:'''           
#add BB button
def add_bb():
    imgCanvas.bind('<Button-1>', __start_bb)
    imgCanvas.bind('<ButtonRelease-1>', __save_bb)
    imgCanvas.config(cursor='cross')
    remBBButt.config(state=DISABLED)
    helpStatus.config(text="Click-and-drag (starting topleft) to draw a bounding box:")
#draw BB in real-time    
def __start_bb(event):
    global loc1
    imgCanvas.bind('<Motion>', __draw_bb)
    loc1 = (event.x, event.y)
#draw BB rectangle
def __draw_bb(event):
    global loc1
    global images
    global imgcount
    __refreshImg()
    csrLoc = (event.x, event.y)
    coords = [loc1[0], loc1[1], csrLoc[0], csrLoc[1]] #can I make this a tuple?
    imgCanvas.create_rectangle(coords, outline="red", fill="", width=3)
#save BB and create individual imgdict entry
def __save_bb(event):
    global loc1
    global loc2
    imgCanvas.unbind('<Motion>')
    imgCanvas.unbind('<Button-1>')
    imgCanvas.unbind('<ButtonRelease-1>')
    loc2 = (event.x, event.y)
    imgdict[imgcount]['box'].append([loc1[0], loc1[1], loc2[0], loc2[1]]) #save BB coords for image
    im = Image.fromarray(imgdict[imgcount]['img']).resize((512, 512))
    coords = (loc1[0], loc1[1], loc2[0], loc2[1]) #4-tuple form for cropping
    im = im.crop(coords)
    inds[imgcount].append(ImageTk.PhotoImage(im.resize((512, 512)))) #append cropped image to inds dictionary for Tk storage
    imgdict[imgcount]['lbl'].append([])
    imgdict[imgcount]['val'].append([])
    imgCanvas.config(cursor='')
    remBBButt.config(state=NORMAL)
    lblIndsButt.config(state=NORMAL)
    helpStatus.config(text="Bounding box saved. Click on \"Label Individuals\" when finished.")
    #print(loc1, loc2)
#remove BB button
def rem_bb():
    imgCanvas.bind('<Button-1>', __del_bb)
    imgCanvas.config(cursor="pirate")
    addBBButt.config(state=DISABLED)
    helpStatus.config(text="Click near the center of the bounding box you want to delete:")
#delete BB
def __del_bb(event):
    imgCanvas.unbind('<Button-1>')
    selX = event.x
    selY = event.y
    #print("Selected coords:", selX, selY)
    boxcount, cBox = 0, 0
    dist = 100
    for box in imgdict[imgcount]['box']:
        xc = (box[0] + box[2])/2
        yc = (box[1] + box[3])/2
        #print("Center coords:", xc, yc)
        cDist = math.sqrt((selX-xc)**2 + (selY-yc)**2)
        if dist > cDist:
            cBox = boxcount
            dist = cDist
        boxcount += 1
    del imgdict[imgcount]['box'][cBox] #delete bounding box
    del imgdict[imgcount]['lbl'][cBox] #delete individual's labels
    del imgdict[imgcount]['val'][cBox] #delete individual's symptom values
    del inds[imgcount][cBox] #delete inds Tk image
    __refreshImg()
    imgCanvas.config(cursor="")
    addBBButt.config(state=NORMAL)
    helpStatus.config(text="Bounding box deleted.")
#update image BBs
def __refreshImg():
    imgCanvas.delete('all')
    imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
    for loc in imgdict[imgcount]['box']:
        imgCanvas.create_rectangle(loc, outline="red", fill="", width=3)

'''Labels:'''
#parse labels.txt - NOTE: user needs to have spaces after "LABEL:" & "INFO:"
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
def __addLbls():
    for l in range(len(lbls)):
        if len(lFrames) != len(lbls):#create lFrames
            lFrames[l], sVars[l], vVars[l], nVars[l] = __createLbl(l)
        else:#redraw lFrames
            for widget in lFrames[l].winfo_children():
                if widget.winfo_class() == "Radiobutton":
                    if widget['text'] in imgdict[imgcount]['lbl'][indcount]:
                        labelNdx = imgdict[imgcount]['lbl'][indcount].index(widget['text'])
                        val = imgdict[imgcount]['val'][indcount][labelNdx]
                        name = lbls[l]['name']
                        sVars[l].set(1)
                        vVars[l].set(val)
                        nVars[l].set(name+": %0.2f"%val)
                elif (widget.winfo_class() == "Label") and (widget['text'] == "/\\"): #change eLabel to extend
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
    resButt = Button(lFrame, text="Reset", command=lambda : reset(n), anchor=E, padx=1)
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
    if name in imgdict[imgcount]['lbl'][indcount]: #clean imgdict records
        labelNdx = imgdict[imgcount]['lbl'][indcount].index(name)
        del imgdict[imgcount]['lbl'][indcount][labelNdx] #delete individual's labels
        del imgdict[imgcount]['val'][indcount][labelNdx] #delete individual's symptom values
    retract()
    helpStatus.config(text="Reset variables for %s."%name)
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
    name = lbls[n]['name']
    desc = lbls[n]['desc']
    exam = lbls[n]['exam']
    opt = lbls[n]['opt'] if ('opt' in lbls[n]) else None
    for f in range(len(lFrames)):
        lFrames[f].grid_forget() #could be more specific here
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
    dFrame.grid(row=crow, column=0, sticky="nsew", columnspan=2)
    crow+=1
    textbox = tkst.ScrolledText(dFrame, wrap=WORD, height=5, width=25)
    textbox.insert(INSERT, desc) 
    textbox.grid(row=0, column=0, sticky="nsew")
    textbox.config(state=DISABLED)
    #dLabel = Label(dFrame, text=desc, height=3, width=50) text cut off
    #dLabel.grid(row=0, column=0, sticky="nsew")
    pLabel2 = Label(lFrames[n], pady=1) #padding label 2
    pLabel2.grid(row=crow, column=0)
    crow+=1
    xFrame = LabelFrame(lFrames[n], text="Examples") #examples frame
    xFrame.grid(row=crow, column=0, sticky="nsew", columnspan=2)
    crow+=1
    xLabel = Label(xFrame, text=exam)
    xLabel.grid(row=0, column=0, sticky="nsew")    
    #add loop for slideshow example images with option for see more 
    #which if no appropriate dir is found just pulls up a google images search of the symptom   
#retract extended info    
def retract():
    __clrLbls()
    __addLbls()
    helpStatus.config(text="Labeling Individual %d of %d."%(indcount+1, len(inds[imgcount])))
    #__printVars()
#select label
def selLbl(n):
    if 'opt' not in lbls[n]:
        vVars[n].set(1)
        nVars[n].set(lbls[n]['name']+":1.0")
    else:
        extend(n)
    helpStatus.config(text="Selected %s."%lbls[n]['name'])
#extend label
def extLbl(n):
    helpStatus.config(text="Extended %s."%lbls[n]['name'])
    extend(n)
#option select   
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
    helpStatus.config(text="Set value of "+lbls[varNum]['name']+" to %0.2f"%value)
#slider response
def selSld(n):
    name = lbls[n]['name']
    val = vVars[n].get()
    for wid in lFrames[n].winfo_children():
        if wid.winfo_class() == "Radiobutton":
            wid.select()
    nVars[n].set(name+": %0.2f"%val)
    helpStatus.config(text="Set value of "+name+" to %0.2f"%val)

'''Labeling Modes:'''
#draw bounding boxes mode
def __bnd_inds():
    global imgCanvas
    imgCanvas.grid_forget()
    imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
    imgCanvas.grid(row=0, column=0, columnspan=2)
    nextButt.config(command=nextImg)
    prevButt.config(command=backImg)
    nextButt.config(text="Next Image")
    prevButt.config(text="Previous Image")
    if imgcount != 0:
        prevButt.config(state=NORMAL)
    else:
        prevButt.config(state=DISABLED)
    if len(images) - 1 == imgcount:
        nextButt.config(text="Save & Exit")
        nextButt.config(command=pklAll)
    prevButt.grid(row=1, column=0, sticky="nsew")
    nextButt.grid(row=1, column=1, sticky="nsew")    
#label individuals mode
def __lbl_inds():
    global imgCanvas
    imgCanvas.grid_forget()
    imgCanvas.create_image(0, 0, image=inds[imgcount][indcount], anchor=NW)
    imgCanvas.grid(row=0, column=0, columnspan=2)
    prevButt.config(command=lambda: backImg(True))
    if len(inds[imgcount]) != 1:
        nextButt.config(text="Next Individual")
        nextButt.config(command=lambda: nextImg(True))
    elif len(images) - 1 == imgcount:
        nextButt.config(text="Save & Exit")
        nextButt.config(command=pklAll)
    elif len(inds[imgcount]) - 1 == indcount:
        nextButt.config(text="Next Image")
        nextButt.config(command=nextImg)
    if imgcount != 0:
        prevButt.config(state=NORMAL)
    else:
        prevButt.config(state=DISABLED)
    if indcount != 0:
        prevButt.config(command=lambda: backImg(True))
        prevButt.config(text="Previous Individual")
    else:
        prevButt.config(command = backImg)
        prevButt.config(text="Previous Image")
    prevButt.grid(row=1, column=0, sticky="nsew")
    nextButt.grid(row=1, column=1, sticky="nsew")
    #change labels to save per individual   
#switch between bounding box and labeling modes
def __selMode(mode):
    if mode == "BB":
        m.geometry("750x660")
        lblButt.config(relief=RAISED)
        bbButt.config(relief=SUNKEN)
        if len(lFrames) != 0:
            __clrVars()
            __clrLbls()
        addBBButt.grid(row=0, column=0, sticky="nsew", pady=60)
        remBBButt.grid(row=1, column=0, sticky="nsew", pady=60)
        lblIndsButt.grid(row=2, column=0, sticky="nsew", pady=60)
        __bnd_inds()
        __refreshImg()
        helpStatus.config(text="Draw bounding boxes for all individuals then click on \"Label Individuals\" button.")
    elif mode == "SL":
        m.geometry("775x685")
        lblButt.config(state=NORMAL)
        bbButt.config(relief=RAISED)
        lblButt.config(relief=SUNKEN)
        #__clrVars()
        __clrLbls()
        __addLbls()
        __lbl_inds()
        helpStatus.config(text="Labeling Individual %d of %d."%(indcount+1, len(inds[imgcount])))

'''Data:'''
#print selection/value variables for debug purposes
def __printVars():
    global nVars
    global vVars
    global sVars
    print("Variables:")
    for s in range(sVars):
            try:
                if sVars[s].get() == 1:
                    print("%s: %d"%(nVars[s].get(), vVars[s].get()))
            except:
                try:
                    print("Couldn't get variables for %s"%nVars[s]) 
                except:
                    print("Couldn't get variables #%d"%s) 
#clear/save variables to imgdict
def __clrVars():
    global imgdict
    global vVars
    global nVars
    n = 0
    for val in vVars:
        if vVars[val].get() != 0:
            lname = nVars[n].get().split(":")[0]
            imgdict[imgcount]['lbl'][indcount].append(lname)
            imgdict[imgcount]['val'][indcount].append(vVars[val].get())
        n += 1
    for i in range(len(lbls)):
        vVars[i].set(0)
        sVars[i].set(0)
        nVars[i].set(lbls[i]['name'])
    #print(imgdict[imgcount])       
#pickles image dictionary entry 
def __pklImg(imgNum):
    try:
        #print("Trying to pickle image #%d: %s"%(imgNum, "".join(lims[imgNum].rsplit(".", 1))))
        if os.path.isfile(os.path.join(cdir, "pickles/%s.pickle"%"".join(lims[imgNum].rsplit(".", 1)))): #wiping previous pickle versions
            #print("Removing old version...")
            os.remove(os.path.join(cdir, "pickles/%s.pickle"%"".join(lims[imgNum].rsplit(".", 1))))
        with open("pickles/%s.pickle"%"".join(lims[imgNum].rsplit(".", 1)),"wb") as pickle_out: #writing new pickles
            pickle.dump(imgdict[imgNum], pickle_out)
    except:
        print("Couldn't pickle img #%d: %s"%(imgNum, "".join(lims[imgNum].rsplit(".", 1))))
#pickles all unsaved images and exits
def pklAll():
    for n_image in imgdict: #check each image for whether any labels were selected
        if imgdict[n_image]['val']:
            __pklImg(n_image)
    print("Done.")
    m.quit()
#print pickle files for debug purposes
def readPkl():
    pass

#open window in top left of screen
def __topleft_window(width=750, height=660):
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
imgdict, inds = {}, {} #Image Dictionary Attributes: img, box, lbl, val
images = [] #temporary storage for Tkinter images
imgcount, indcount = 0, 0
for im in lims:
    imgdict[imgcount] = {"img":np.asarray(Image.open(os.path.join(idir, im))), "box":[], "lbl":[], "val":[]}
    inds[imgcount] = [] #storage dictionary for individual images
    images.append(ImageTk.PhotoImage(Image.open(os.path.join(idir, im)).resize((512,512)))) #should Image.fromarray(imgdict[imgcount]['img']).resize((512, 512)) be used instead of opening?
    imgcount += 1
imgcount = 0
loc1, loc2 = (0, 0), (0, 0) #storage containers for cursor locations
#labeling mode button frame/configuration
modeButts = LabelFrame(m, text="Label Mode", bd=0, labelanchor=N) #mode selector top bar
modeButts.grid(row=0, column=0, columnspan=2, sticky="nsew")
modeButts.grid_columnconfigure(0, weight=1)
modeButts.grid_columnconfigure(1, weight=1)
#labeling mode buttons
bbButt = Button(modeButts, text="Bounding Boxes", command=lambda : __selMode("BB"))
bbButt.grid(row=0, column=0, sticky="nsew")
lblButt = Button(modeButts, text="Symptom Labels", command=lambda : __selMode("SL"), state=DISABLED)
lblButt.grid(row=0, column=1, sticky="nsew")
#image/labels column configuration
imgFrame = Frame(m, padx=2)
imgFrame.grid(row=1, column=0)
lblFrame = LabelFrame(m, padx=2)
lblFrame.grid(row=1, column=1, sticky="nsew")
m.grid_columnconfigure(1, weight=1)
lblFrame.grid_columnconfigure(0, weight=1)
#image canvaas
imgCanvas = Canvas(imgFrame, width=512, height=512)
imgCanvas.create_image(0, 0, image=images[0], anchor=NW)
imgCanvas.grid(row=0, column=0, columnspan=2)
#image buttons
prevButt = Button(imgFrame, text="Last Image", state=DISABLED, padx=15, pady=15)
nextButt = Button(imgFrame, text="Next Image", command=nextImg, padx=15, pady=15)
prevButt.grid(row=1, column=0, sticky="nsew")
nextButt.grid(row=1, column=1, sticky="nsew")
#help bar
helpBar = LabelFrame(imgFrame, text="Help") #image progress and directions displayer
helpBar.grid(row=2, column=0, columnspan=2, sticky="nsew")
helpStatus = Label(helpBar, text="This is where help info goes.", anchor=W, bd=1)
helpStatus.grid(row=0, column=0, sticky="nsew")
#bounding box buttons
addBBButt = Button(lblFrame, text="Add Bounding Box", command=add_bb, padx=20, pady=15)
remBBButt = Button(lblFrame, text="Remove Bounding Box", command=rem_bb, padx=20, pady=15, state=DISABLED)
lblIndsButt = Button(lblFrame, text="Label Individuals", command=lambda: __selMode("SL"), padx=5, pady=15, state=DISABLED)
#labels.txt dictionary  
lbls = __parseLbls(lblinfopath) 
#label frame storage
lFrames, sVars, vVars, nVars = {}, {}, {}, {} 
#m.resizable(True, True)
__topleft_window(750, 660)
__selMode("BB")
m.mainloop()

#Example Image Dictionary Entry:
'''
{
    "img":nparr,
    "box":coordlist,
    "lbl":lblnames,
    "val: lblvec
}
To Choose Video to Annotate:
filedialog.askopenfilename(initialdir="/", title="Select Video File (mp3/mp4)",
                           filetypes=(("videos", ".mp3 .mp4"), ("all files", "*.*"))) #this might have to be separated with same "videos" name e.g. ("videos", ".mp4")
'''
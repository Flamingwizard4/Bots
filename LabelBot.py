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


import os, re
from tkinter import *
from PIL import ImageTk, Image, ImageDraw
#import cv2
#import cv2.cv as cv
from time import time, sleep

m = Tk() #main window
m.title("LabelBot - Dataset Creation GUI")
#m.geometry("600x600")
#m.iconbitmap(logo.ico)

cdir = os.getcwd()
ldir = os.path.join(cdir, "labels", "unlabeled_images")#are these stored as numpy arrays in csv files or as real pictures??
lblinfopath = os.path.join(cdir, "labels", "labels.txt")   
#images to label
lims = os.listdir(ldir)
imgcount = 0
images, boxes = [], [] #changes boxes to dictionary
for im in lims:
    images.append(ImageTk.PhotoImage(Image.open(os.path.join(ldir, im)).resize((512,512)))) #change to storing images as numpy arrays in dictionaries
print("There are %d images to label."%len(images))

loc1 = (0, 0) #storage container for 1st cursor location
loc2 = (0, 0) #2nd cursor location

#parses labels.txt - needs to have spaces after LABEL:/INFO: 
#add $ detector for spectrum symptoms
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
    imgCanvas.grid(row=0, column=0, columnspan=3)
    
    if imgcount == len(lims) - 1:
        nextImgButt.grid_forget()
        nextImgButt = Button(imgFrame, text="Exit", command=m.quit, padx=20, pady=15)
        nextImgButt.grid(row=1, column=2)
    else:
        nextImgButt.grid_forget()
        nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
        nextImgButt.grid(row=1, column=2)
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
    imgCanvas.grid(row=0, column=0, columnspan=3)
    
    if imgcount == 0:
        backImgButt.grid_forget()
        backImgButt = Button(imgFrame, text="Last Image", command=backImg, padx=20, pady=15, state=DISABLED)
        backImgButt.grid(row=1, column=0)
    else:
        backImgButt.grid_forget()
        backImgButt = Button(imgFrame, text="Last Image", command=backImg, padx=20, pady=15)
        backImgButt.grid(row=1, column=0)
    nextImgButt.grid_forget()
    nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
    nextImgButt.grid(row=1, column=2)
    
    #addCowButt = Button(imgFrame, text="Add Cow", command=addCow, padx=20, pady=15)
    #addCowButt.grid(row=1, column=1) 

#button command functionality
def addCow():
    imgCanvas.bind('<Button-1>', draw_bb)
    imgCanvas.bind('<ButtonRelease-1>', save_bb)

#draw bounding box in real-time    
def draw_bb(event):
    global loc1
    imgCanvas.bind('<Motion>', draw_rec)
    loc1 = (event.x, event.y)
    print("Coords 1: ")
    print(loc1)
    
#draws bounding box rectangle
def draw_rec(event):
    global loc1
    global images
    global imgcount
    global boxes
    imgCanvas.delete('all')
    imgCanvas.create_image(0, 0, image=images[imgcount], anchor=NW)
    if boxes:
        for loc in boxes:
            imgCanvas.create_rectangle(loc, outline="red", fill="", width=3)
    cursorLoc = (event.x, event.y)
    coords = [loc1[0], loc1[1], cursorLoc[0], cursorLoc[1]]
    #print(coords)
    imgCanvas.create_rectangle(coords, outline="red", fill="", width=3)
    
def save_bb(event):
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
    
def extend():
    print("Extended.")
    
def __addSymptom(name, desc, slider=False, options=None):
    symFrame = Frame(lblFrame, padx=50, pady=10)
    symFrame.grid(row=1, column=0)
    sVar = IntVar()
    #contents
    s = Radiobutton(symFrame, text=name, variable=sVar)
    s.grid(row=0, column=0)
    sReset = Button(symFrame, text="Reset", command=lambda: sVar.set(0), anchor=E)
    sReset.grid(row=0, column=1)
    sButt = Button(symFrame, text="\/", command=extend)
    sButt.grid(row=1, column=0, columnspan=2)
    return symFrame, sVar
    
"""WIDGETS:"""

'''
myButton = Button(m, text="Don't Click", command=buttFunc, padx=40, pady=20) #fg is text color, bg is background color
myButton.grid(row=1, column=1)
'''

imgFrame = LabelFrame(m, text="Image Frame", padx=5, pady=5)
imgFrame.grid(row=0, column=0)
lblFrame = LabelFrame(m, text="Label Frame", padx=5, pady=5)
lblFrame.grid(row=0, column=1)

imgCanvas = Canvas(imgFrame, width=512, height=512)
imgCanvas.create_image(0, 0, image=images[0], anchor=NW)
imgCanvas.grid(row=0, column=0, columnspan=3)


backImgButt = Button(imgFrame, text="Last Image", state=DISABLED, padx=20, pady=15)
backImgButt.grid(row=1, column=0)

nextImgButt = Button(imgFrame, text="Next Image", command=nextImg, padx=20, pady=15)
nextImgButt.grid(row=1, column=2)

addCowButt = Button(imgFrame, text="Add Cow", command=addCow, padx=20, pady=15)
addCowButt.grid(row=1, column=1)

#parsing labels.txt   
lbls = parseLabels(lblinfopath)
mySymptoms = Label(lblFrame, text="Symptoms:")
mySymptoms.grid(row=0, column=0) #columnspan=

symFrames = {}
symVars = {}
for l in range(len(lbls)):
    spectrum = False
    if "$" in lbls[l]['name']:
        spectrum = True
        lbls[l]['name'] = lbls[l]['name'][:-2]
    if len(lbls[l]) == 3:  
        symFrames[l], symVars[l] = __addSymptom(lbls[l]['name'], lbls[l]['desc'], spectrum, lbls[l]['opt'])
    elif len(lbls[l]) == 2:
        symFrames[l], symVars[l] = __addSymptom(lbls[l]['name'], lbls[l]['desc'], spectrum)
    symFrames[l].grid(row=l, column=0)


m.mainloop()
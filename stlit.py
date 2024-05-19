
import math
import streamlit as st
from PIL import Image
from PIL import ImageDraw
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_js_eval import streamlit_js_eval


def marker(point,tomark,another):
    if list(point) not in st.session_state[tomark] and list(point) not in st.session_state[another]:
        st.session_state[tomark].append([point[0],point[1]])
        st.experimental_rerun()

def getdist(pos1, pos2):
    return math.dist(pos1, pos2)

def stage3():
    if len(st.session_state['pos']) > 1:
        for i in range(len(st.session_state['pos']) - 1):
            st.session_state['heightinpixel'].append(getdist(st.session_state['pos'][i], st.session_state['pos'][i + 1]))
    
    for i in range(len(st.session_state['heightinpixel'])):
        st.session_state['heightsum'] += st.session_state['heightinpixel'][i]

        if st.session_state['refincm'] != 0 and st.session_state['refpos'] != []:
            st.session_state['refincm'] = float(st.session_state['refincm'])
            st.session_state.stage = 3
            st.session_state['img'] = imgraw


        elif st.session_state['refpos'] == []:
            st.text("please mark the locations")
        elif st.session_state['refincm'] == 0:
            st.text("please input height of the reference object")
        elif st.session_state['refpos'] == []:
            st.text("please mark the positions of the reference object")

def undo():
    if len(st.session_state["pos"]) > 0 and st.session_state['currentmark']=='person':
        st.session_state["pos"].pop()
    elif len(st.session_state["refpos"]) > 0 and st.session_state['currentmark']=='object':
        st.session_state["refpos"].pop()
    st.rerun()

if "stage" not in st.session_state:
    st.session_state.stage = 0

if 'pos' not in st.session_state:
    st.session_state['pos'] = []

if 'refpos' not in st.session_state:
    st.session_state['refpos'] = []

if 'refinpixel' not in st.session_state:
    st.session_state['refinpixel'] = []

if 'refsum' not in st.session_state:
    st.session_state['refsum'] = 0

if 'img' not in st.session_state:
    st.session_state['img'] = None

if 'heightinpixel' not in st.session_state:
    st.session_state['heightinpixel'] = []

if 'heightsum' not in st.session_state:
    st.session_state['heightsum'] = 0

if 'currentmark' not in st.session_state:
    st.session_state['currentmark'] = 'person'

# Add JavaScript to listen for Ctrl + Z and call the undo function
undo_js = """
document.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.key === 'z') {
        window.streamlitApi.runMethod('undo')
    }
});
"""
streamlit_js_eval(js_expressions=undo_js)

st.title("Height Estimating")

if st.session_state.stage==0:
    option = st.selectbox("Choose image source", ("Upload an image", "Capture from webcam"))

    if option == "Upload an image":
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            imgraw = Image.open(uploaded_file)
            imgraw = imgraw.resize((600, 600))
            st.session_state['img'] = np.array(imgraw)
    elif option == "Capture from webcam":
        try:
            camera_image = st.camera_input("Take a picture")
            if camera_image is not None:
                imgraw = Image.open(camera_image)
                st.session_state['img'] = np.array(imgraw)
            else:
                st.warning("Please capture an image using the webcam.")
        except Exception as e:
            st.error(f"Error accessing the camera: {e}")

    if st.session_state['img'] is not None:
        imgraw = Image.fromarray(st.session_state['img'])

        st.session_state['img'] = np.array(imgraw)
        col1,col2,col3,col4 = st.columns(4)


        with imgraw:
            st.text("click to mark positions of your bodyparts")
            draw = ImageDraw.Draw(imgraw)

            with col1:
                if st.button("undo"):
                    undo()
            with col2:
                if st.button("person"):
                    st.session_state["currentmark"]='person'
            with col3:
                if st.button("object"):
                    st.session_state['currentmark']='object'
            with col4:
                if st.button('reset'):
                    streamlit_js_eval(js_expressions="parent.window.location.reload()") # F5

            st.text("currently working on: "+st.session_state['currentmark'])

            redpositionmarked = len(st.session_state["pos"])
            bluepositionmarked = len(st.session_state['refpos'])

            # count position marked then draw circle
            for i in range(redpositionmarked):
                circle = [st.session_state["pos"][i][0] - 3, st.session_state["pos"][i][1] - 3, st.session_state["pos"][i][0] + 3, st.session_state["pos"][i][1] + 3]
                draw.ellipse(circle, fill="red")

            for i in range(bluepositionmarked):
                circle = [st.session_state["refpos"][i][0] - 3, st.session_state["refpos"][i][1] - 3, st.session_state["refpos"][i][0] + 3, st.session_state["refpos"][i][1] + 3]
                draw.ellipse(circle, fill=(0,0,255))

            # draw line
            if redpositionmarked > 1:
                for i in range(redpositionmarked - 1):
                    draw.line([st.session_state['pos'][i][0], st.session_state['pos'][i][1], st.session_state['pos'][i + 1][0], st.session_state['pos'][i + 1][1]], fill="red", width=0)

            if bluepositionmarked >1:
                for i in range(bluepositionmarked-1):
                    draw.line([st.session_state['refpos'][i][0], st.session_state['refpos'][i][1], st.session_state['refpos'][i + 1][0], st.session_state['refpos'][i + 1][1]], fill=(0,0,255), width=0)

            value = streamlit_image_coordinates(imgraw, key="pil")

            if value is not None:
                point = value["x"], value["y"]
                # check which state to process
                if st.session_state['currentmark'] == 'person':
                    marker(point, 'pos', 'refpos')

                elif st.session_state['currentmark'] == 'object':
                    marker(point, 'refpos', 'pos')        

        st.session_state['refincm'] = st.number_input("input height of the reference object (cm)")
        st.button("continue", on_click=stage3)

if st.session_state.stage == 3:
    img = st.session_state['img']
    for i in range(len(st.session_state['refpos']) - 1):
        st.session_state['refinpixel'].append(getdist(st.session_state['refpos'][i], st.session_state['refpos'][i + 1]))

    for i in range(len(st.session_state['refinpixel'])):
        st.session_state['refsum'] += st.session_state['refinpixel'][i]

    # calculation
    pixel_per_cm = st.session_state['refincm'] / st.session_state['refsum']
    heightestimated = st.session_state['heightsum'] * pixel_per_cm

    st.image(img)
    st.text('the estimated height is ' + str(int(heightestimated)) + 'cm')
    if st.button('back to main page'):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

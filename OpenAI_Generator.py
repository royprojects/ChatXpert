"""
ChatGPT & DALL·E using openai API (by T.-W. Yoon, Mar. 2023)
"""

import openai
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from langdetect import detect
from gtts import gTTS
# from io import BytesIO
# import clipboard

# initial prompt for gpt3.5
initial_prompt = [
    {"role": "system", "content": "You are a helpful assistant."}
]


def openai_create_text(
        user_prompt,
        temperature=0.7,
        model="gpt-3.5-turbo",
        authen=True
    ):
    """
    This function generates text based on user input
    if authen is True.

    Args:
        user_prompt (string): User input
        temperature (float): Value between 0 and 2. Defaults to 0.7
        model (string): "gpt-3.5-turbo" or "gpt-4"
        authen (bool): Defaults to True.

    The results are stored in st.session_state variables.
    """

    if not authen or user_prompt == "":
        return None

    # Add the user input to the prompt
    st.session_state.prompt.append(
        {"role": "user", "content": user_prompt}
    )

    try:
        with st.spinner("AI is thinking..."):
            response = openai.ChatCompletion.create(
                model=model,
                messages=st.session_state.prompt,
                temperature=temperature,
                # max_tokens=4096,
                # top_p=1,
                # frequency_penalty=0,
                # presence_penalty=0.6,
            )
        generated_text = response.choices[0].message.content
    except openai.error.OpenAIError as e:
        generated_text = None
        st.error(f"An error occurred: {e}", icon="🚨")

    if generated_text:
        # Add the generated output to the prompt
        st.session_state.prompt.append(
            {"role": "assistant", "content": generated_text}
        )
        st.session_state.generated_text = generated_text

    return None


def openai_create_image(description, size="image_size", authen=True):
    """
    This function generates image based on user description
    if authen is True.

    Args:
        description (string): User description
        size (string): Pixel size of the generated image

    The resulting image is plotted.
    """

    if not authen or description.strip() == "":
        return None

    try:
        with st.spinner("AI is generating..."):
            response = openai.Image.create(
                prompt=description,
                n=1,
                size=size
            )
        image_url = response['data'][0]['url']
        st.image(
            image=image_url,
            use_column_width=True
        )
    except openai.error.OpenAIError as e:
        st.error(f"An error occurred: {e}", icon="🚨")

    return None


def reset_conversation():
    # to_clipboard = ""
    # for (human, ai) in zip(st.session_state.human_enq, st.session_state.ai_resp):
    #    to_clipboard += "\nHuman: " + human + "\n"
    #    to_clipboard += "\nAI: " + ai + "\n"
    # clipboard.copy(to_clipboard)

    st.session_state.generated_text = None
    st.session_state.prompt = initial_prompt
    st.session_state.human_enq = []
    st.session_state.ai_resp = []
    st.session_state.initial_temp = 0.7
    st.session_state.input_key = 0


def switch_between_two_apps():
    st.session_state.initial_temp = st.session_state.temp_value
    st.session_state.pre_audio_bytes = None
    st.session_state.input_key = 0


def create_text(authen, model):
    """
    This function geneates text based on user input
    by calling openai_create_text()
    if user password is valid (authen = True).

    model is set to "gpt-3.5-turbo" or "gpt-4".
    """

    if "generated_text" not in st.session_state:
        st.session_state.generated_text = None

    if "prompt" not in st.session_state:
        st.session_state.prompt = initial_prompt

    if "human_enq" not in st.session_state:
        st.session_state.human_enq = []

    if "ai_resp" not in st.session_state:
        st.session_state.ai_resp = []

    if "initial_temp" not in st.session_state:
        st.session_state.initial_temp = 0.7

    if "pre_audio_bytes" not in st.session_state:
        st.session_state.pre_audio_bytes = None

    if "input_key" not in st.session_state:
        st.session_state.input_key = 0

    with st.sidebar:
        st.write("")
        st.write("**Text to Speech**")
        st.session_state.tts = st.radio(
            "$\\hspace{0.08em}\\texttt{TTS}$",
            ('Enabled', 'Disabled'),
            # horizontal=True,
            index=1, label_visibility="collapsed"
        )
        st.write("")
        st.write("**Temperature**")
        st.session_state.temp_value = st.slider(
            label="$\\hspace{0.08em}\\texttt{Temperature}\,$ (higher $\Rightarrow$ more random)",
            min_value=0.0, max_value=2.0, value=st.session_state.initial_temp,
            step=0.1, format="%.1f",
            label_visibility="collapsed"
        )
        st.write("(Higher $\Rightarrow$ More random)")

    st.write("")
    left, right = st.columns([2, 3])
    left.write("##### Conversations with AI")
    right.write("(free to ask)")

    # for (human, ai) in zip(st.session_state.human_enq, st.session_state.ai_resp):
    #    st.write("**:blue[Human:]** " + human)
    #    st.write("**:blue[AI:]** " + ai)

    # Get the text description from the user
    key = st.session_state.input_key
    st.text_area(
        label="$\\hspace{0.08em}\\texttt{Enter your query}$",
        value="",
        label_visibility="visible",
        key=key
    )
    user_input_stripped = st.session_state[key-1].strip() if key > 0 else ""

    left, right = st.columns(2) # To show the results below the button
    left.button(
        label="Send",
        on_click=openai_create_text(
            user_input_stripped,
            temperature=st.session_state.temp_value,
            model=model,
            authen=authen
        )
    )
    right.button(
        label="Reset",
        on_click=reset_conversation
    )

    # Use your microphone
    audio_bytes = audio_recorder(
        pause_threshold=2.0,
        # sample_rate=sr,
        text="Speak",
        recording_color="#e87070",
        neutral_color="#6aa36f",
        # icon_name="user",
        icon_size="2x",
    )

    if authen:
        if audio_bytes != st.session_state.pre_audio_bytes:
            try:
                audio_file = "files/recorded_audio.wav"
                with open(audio_file, "wb") as recorded_file:
                    recorded_file.write(audio_bytes)
                audio_data = open(audio_file, "rb")

                # audio_data = BytesIO(audio_bytes)
                # audio_data.name = "recorded_audio.wav"

                transcript = openai.Audio.transcribe("whisper-1", audio_data)

                user_input_stripped = transcript['text']
                openai_create_text(
                    user_input_stripped,
                    temperature=st.session_state.temp_value,
                    model=model,
                    authen=authen
                )
                # st.write("**:blue[Human:]** " + user_input_stripped)
            except Exception as e:
                st.error(f"An error occurred: {e}", icon="🚨")
            st.session_state.pre_audio_bytes = audio_bytes

        if user_input_stripped != "" and st.session_state.generated_text:
            # st.write("**:blue[AI:]** " + st.session_state.generated_text)
            # TTS
            if st.session_state.tts == 'Enabled':
                try:
                    with st.spinner("TTS in progress..."):
                        lang = detect(st.session_state.generated_text)
                        tts = gTTS(text=st.session_state.generated_text, lang=lang)
                        text_audio_file = "files/output_text.wav"
                        tts.save(text_audio_file)
                        # text_audio_file = BytesIO()
                        # tts.write_to_fp(text_audio_file)
                    st.audio(text_audio_file)
                    # st.audio(text_audio_file.getvalue())
                except Exception as e:
                    st.error(f"An error occurred: {e}", icon="🚨")

            st.session_state.human_enq.append(user_input_stripped)
            st.session_state.ai_resp.append(st.session_state.generated_text)
            # clipboard.copy(st.session_state.generated_text)

    for (human, ai) in zip(st.session_state.human_enq[::-1], st.session_state.ai_resp[::-1]):
        st.write("**:blue[Human:]** " + human)
        st.write("**:blue[AI:]** " + ai)
        st.write("---")

    st.session_state.input_key += 1


def create_image(authen, num_image ,image_size):
    """
    This function geneates image based on user description
    by calling openai_create_image()
    if user password is valid (authen = True).
    """

    # Set the image size
    with st.sidebar:
        st.write("")
        st.write("**Pixel size**")
        image_size = st.radio(
            "$\\hspace{0.1em}\\texttt{Pixel size}$",
            ('256x256', '512x512', '1024x1024'),
            # horizontal=True,
            index=1,
            label_visibility="collapsed"
        )
    with st.sidebar:
        st.write("")
        st.write("**select number of images**")
        num_image = st.selectbox('enter the number of images to be generated', (1, 2, 3, 4))
        


        

    # Get the image description from the user
    st.write("")
    st.write(f"##### Description for your image (in English)")
    description = st.text_area(
        label="$\\hspace{0.1em}\\texttt{Description for your image}\,$ (in $\,$English)",
        # value="",
        label_visibility="collapsed"
    )

    left, _ = st.columns(2) # To show the results below the button
    left.button(
        label="Generate",
        on_click=openai_create_image(description, num_image ,image_size)
    )


def openai_create():
    """
    This main function generates text or image by calling
    openai_create_text() or openai_create_image(), respectively.
    """
    st.write("## 🎭 CHAT-XPERT")

    with st.sidebar:
        st.write("")
        st.write("**Choic of API key**")
        choice_api = st.sidebar.radio(
            "$\\hspace{0.25em}\\texttt{Choic of API}$",
            ('Your key', 'My key'),
            label_visibility="collapsed",
            horizontal=True,
            on_change=reset_conversation
        )

        if choice_api == 'Your key':
            st.write("**Your API Key**")
            openai.api_key = st.text_input(
                label="$\\hspace{0.25em}\\texttt{Your OpenAI API Key}$",
                type="password",
                label_visibility="collapsed"
            )
            # st.write("You can obtain an API key from https://beta.openai.com")
            authen = True
        else:
            openai.api_key = st.secrets["pass"]
            stored_pin = st.secrets["USER_PIN"]
            st.write("**password**")
            user_pin = st.text_input(
                label="Enter password", type="password", label_visibility="collapsed"
            )
            authen = user_pin == stored_pin

        st.write("")
        st.write("**What to Generate**")
        option = st.sidebar.radio(
            "$\\hspace{0.25em}\\texttt{What to generate}$",
            ('Text (GPT 3.5)', 'Image (DALL·E)'),
            label_visibility="collapsed",
            # horizontal=True,
            on_change=switch_between_two_apps
        )

    if option == 'Text (GPT 3.5)':
        create_text(authen, "gpt-3.5-turbo")
    
    else:
        create_image(authen)

    with st.sidebar:
        st.write("")
        st.write("**:blue[Royston 2023]**")

    if not authen:
        st.error("**Incorrect password. Please try again.**", icon="🚨")


if __name__ == "__main__":
    openai_create()

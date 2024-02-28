from flask import Flask, render_template, request,session
import openai
 

# Assuming the OpenAI API key is set securely in your environment variables
openai.api_key = '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'  # Use environment variable for security
app = Flask(__name__)
app.secret_key = 'a637889abbjnasgtejkjndh'

def is_content_safe(text):
    try:
        result = openai.Moderation.create(input=text)
        return not any(category['flagged'] for category in result['results'])
    except Exception as e:
        print(f"Error checking content safety: {e}")
        return True

def start_chat_session(topic):
    try:
        instructions = f"""You are an expert information specialist, provide a detailed overview of the topic and create a question about it. Start the question on a new line with "Qn:" It can be a yes/no, who/what/where/when/how/why, choice, open-ended, true/false, or fill-in-the-blank type. """
        prompt = f"Let's discuss the topic: {topic}."

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt} 
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        print(f"Error in generating chat session content")
        return f"An error occurred while generating content for the topic: {topic}."

def continue_chat_session(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message['content']
    except Exception as e:
        print("Error in generating content: ")
        return "An error occured. Please try again."
        


def assess_user_answer(messages):
    for i in reversed(range(len(messages))):
        if messages[i]['role'] == 'assistant' and messages[i]['content'].startswith('Qn:'):
            last_question = messages[i]['content']
            break
    else:
        last_question = None

    if last_question:
        user_input = last_question + '\n' + messages[-1]['content']
    else:
        user_input = messages[-1]['content']

    # Detailed instructions for AI are not added to the messages list
    prompt = f"""{user_input}
   # As an adept information expert, your role involves evaluating answers and formulating subsequent questions. /
  # Assess the user's response for its correctness and relevance against the backdrop of the prior explanation and query. /
  # Begin by underscoring the initially posed question as derived from the earlier context. / 
  # Upon receiving the user's response, determine its correctness or partial correctness, commencing with "correct"or "partially correct" and then providing an evaluation on the next line. /
  # Should the response be incorrect, initiate with "incorrect" and then deliver your assessment on the following line. /
  # Following the evaluation of the user's response, ALWAYS proceed to pose additional contextually relevant questions. Upon receiving subsequent answers, apply the aforementioned evaluative criteria, persisting in this cycle until the user opts to conclude. Prefix questions with "Qn:" to denote them as such. Evaluate responses in accordance with the guidelines specified above, maintaining this iterative process until cessation by the user. /
  # Question types may include ['"yes" or "no"', '"who", "what", "where", "when", "how", and "why" questions', 'choice questions', 'open-ended questions', '"True" or "False" questions', 'Fill in the blank questions']. Initiate each question with "Qn:" to signify it. Upon receiving an answer, proceed with an evaluation adhering to the stipulated guidelines. Continue this sequence in a loop until the user decides to terminate. /
  # In assessing "yes" or "no" questions, simply classify the user's answer as "correct" or "incorrect", providing a succinct explanation on a new line. /
  # When evaluating "who", "what", "where", "when", "how", and "why" questions, the user's response should be at least one sentence, followed by a concise elucidation of the correct answer. /
  # For choice questions, label the user's answer as "correct" or "incorrect", with a brief clarification of the correct response on a new line. /
  # Open-ended questions require a detailed response, showcasing arguments for and against, with the assessment being critical, categorizing it as "partially correct", "correct", or "incorrect", and then offering a succinct summary of the anticipated answer on the next line. /
  # "True" or "False" questions should be evaluated as either "correct" or "incorrect", accompanied by a brief note on the correct answer on a new line. /
  # For "Fill in the blank" questions, upon the user completing the required word, assess the answer as "correct" or "incorrect", followed by a brief note on the correct answer on a new line. /
  # Adopt a neutral and patient tone as a tutor. /
  # Adhere to the outlined requirements at all times. /
  # Your evaluations should conclude with a concise, point-wise summary. /
    Answer Evaluation:
    """

    # Temporarily create a new message list including the prompt for AI's internal use
    temp_messages = messages.copy()
    temp_messages.append({"role": "system", "content": prompt})
    response = continue_chat_session(temp_messages)

    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        topic = request.form['topic']
        user_answer = request.form.get('user_answer')

        if not topic and not user_answer:
            # If there's an error, only display the error message without any previous messages
            return render_template('index.html', error="Please enter a topic or provide an answer.")

        # Check if the topic is the same as the last one or if it's a new topic
        last_topic = session.get('last_topic')
        if topic and topic != last_topic:
            # Assuming is_content_safe is a function you have defined to check content safety
            if not is_content_safe(topic):
                return render_template('index.html', error="The provided topic contains unsafe content. Please try a different topic.")
            
            # If it's a new topic, reset the messages list for the new topic
            session['messages'] = []  # Reset messages for the new topic
            
            # Assuming start_chat_session is a function you have defined to start a chat
            chat_prompt = start_chat_session(topic)
            session['messages'].append({"role": "system", "content": chat_prompt})
            session['last_topic'] = topic

        if user_answer:
            if not is_content_safe(user_answer):
                return render_template('index.html', error="Your input was found to be unsafe. Please provide a different answer.")
    
            session['messages'].append({"role": "user", "content": user_answer})
            # Assuming assess_user_answer is a function you've defined to evaluate the answer
            evaluation = assess_user_answer(session['messages'])
            session['messages'].append({"role": "assistant", "content": evaluation})

    # Directly pass the current session's messages to the template
    return render_template('index.html', messages=session.get('messages', []), topic=session.get('last_topic', ''))


if __name__ == "__main__":
    app.run(debug=True)

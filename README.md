# Star Wars chatbot API

This is a chatbot API that uses [Star Wars public API](https://swapi.dev/) to feed a chatbot integrated with Claude Sonnet 3.5 hosted and runing on a [AWS Bedrock](https://aws.amazon.com/bedrock/).

The LLM integration uses the Tool Use approach, where the LLM is provided with tools to query external APIs.

- https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages-tool-use.html

In the Star Wars chatbot API, the LLM is provided with the following tools, in the case that model wants to query information about Star Wars universe, specifically about:

- people: https://swapi.dev/api/people/
- planets: https://swapi.dev/api/planets/
- films: https://swapi.dev/api/films/
- species: https://swapi.dev/api/species/
- vehicles: https://swapi.dev/api/vehicles/
- starships: https://swapi.dev/api/starships/

So, if the user asks a question about Star Wars, the model can decide to use one of the tools above to get the information and then answer the user. 

For instance, if the user asks "Who is Luke Skywalker?", the model can decide to use the "people" tool to get the information about Luke Skywalker and then answer the user.

This usecase can be applied to many other usecases, where there are APIs already available and the use of an LLM model can enhance the user experience by providing richer and more accurate responses - or even access to data that the model itself doesn't know about.

# Dependencies

```bash
pip install -r requirements.txt
```

Use [direnv](https://direnv.net/) for local development:

.envrc file example:

```
export ENV=development
export BEDROCK_AWS_PROFILE=your-aws-profile
export BEDROCK_AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
export SW_API_BASE=https://swapi.dev/api/
export MAX_TOKENS=1000
```

```bash
direnv allow .
```

## Login to AWS

Since this API uses AWS Bedrock, you need to login to your AWS account to generate the local environment variables, used by the application to access Bedrock.

- https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html

# Run the app

1) Log in to you AWS account to generate the local environment variables, used by the application to access Bedrock

2) Run the app:

```bash
uvicorn main:app --reload
```

## Run via Docker

```bash
docker build -t star-wars-chatbot-api .
```

```bash
docker run -it --rm \
  -p 8000:8000 \
  -v ~/.aws:/root/.aws \
  -e ENV=development \
  -e BEDROCK_AWS_PROFILE=your-aws-profile \
  -e BEDROCK_AWS_REGION=us-east-1 \
  -e BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0 \
  -e SW_API_BASE=https://swapi.dev/api/ \
  star-wars-chatbot-api
```

## /suggestions endpoint

The /suggestions endpoint is a conversation kickoff. It can be used to suggest questions to the user, so the chat starts easily.

When asking LLM model to suggest questions, it is provided with some context about Star Wars universe, like people and starships. For other usecases, user/feature personalisation context can be provided so the suggestions are more relevant to the conversation.

Send a POST to http://localhost:8000/suggestions/

```bash
curl -N -X POST 'http://localhost:8000/suggestions' \
  -H 'Content-Type: application/json' \
  -d '{"people": "Luke","starships": "X-wing"}'
```

## /chat endpoint

The /chat endpoint is the core feature of this API. 

In this iteration, there is no conversation memory, so each question is treated independently. But, each interaction is provided with tools, so LLM model can get more information by requesting our API to give more data about Star Wars universe before reasoning and answering the user.

Send a POST to http://localhost:8000/chat/

```bash
curl -N -X POST 'http://localhost:8000/chat' \
  -H 'Content-Type: application/json' \
  -d '{"user_input": "How does the X-wing starfighter compare to other ships in the Star Wars universe?"}'
```

## /stream endpoint

The /stream is the streamed version of /chat endpoint. It uses SSE (server-sent events) to dispatch the LLM model responses.

This way, the user interaction is expected to be faster and more interative.

Send a POST to http://localhost:8000/stream/

```bash
curl -N -X POST 'http://localhost:8000/stream' \
  -H 'Content-Type: application/json' \
  -d '{"user_input":"Who was Luke Skywalker and which starships he piloted? Answer in less than 20 words."}'
```

The answer will be streamed back as server-sent events. Like this:

```
data: {"delta": "Sure, I'd be happy to tell you about Luke Skywalker and his starships! Let me check that information for you."}
data: {"tool_event": {"used": true, "names": ["getPeople", "getStarships"]}}
data: {"delta": "Luke"}
data: {"delta": " Skywalker"}
data: {"delta": " was a"}
data: {"delta": " Jedi Knight an"}
data: {"delta": "d hero"}
data: {"delta": " of the Rebel"}
data: {"delta": " Alliance."}
data: {"delta": " He piloted X"}
data: {"delta": "-wings"}
data: {"delta": " an"}
data: {"delta": "d other starships in"}
data: {"delta": " his"}
data: {"delta": " adventures"}
data: {"delta": "."}
data: {"done": true}
```

# Debugging

## Validating AWS Bedrock models

When developing this API, it's really important to validate if the provided AWS credentials have access to Bedrock - and to which models. 

So, there is an API endpoint created to validate and debug that. It shows all models that the credentials can access.

1) Log in to you AWS account to generate the local environment variables, used by the application to access Bedrock
2) Send a GET to http://localhost:8000/debug/bedrock/models
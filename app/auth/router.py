from typing import Annotated

import requests
from fastapi import APIRouter, Form, HTTPException
from pydantic import ValidationError

from .oidc_discovery import oidc_discovery_service
from .schemas import TokenRequest, TokenResponse

router = APIRouter(
    responses={
        200: {"description": "Token response"},
        408: {"description": "Request timeout"},
        502: {"description": "Bad gateway"},
        500: {"description": "Internal server error"},
    }
)


@router.post("/token", response_model=TokenResponse)
def proxy_oauth_token(data: Annotated[TokenRequest, Form()]) -> TokenResponse:
    """
    Proxy endpoint for OAuth token requests to avoid CORS issues.

    This endpoint forwards token requests to the OAuth server and returns the response,
    allowing the frontend to avoid CORS restrictions when requesting tokens.
    """
    try:
        # Get token endpoint from OIDC discovery
        token_endpoint = oidc_discovery_service.get_token_endpoint()

        # Prepare headers for the request
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        # Convert Pydantic model to form data
        form_data = {}
        for key, value in data.model_dump(exclude_none=True).items():
            if value is not None:
                form_data[key] = str(value)

        # Make the request to OAuth server
        response = requests.post(
            token_endpoint,
            data=form_data,
            headers=headers,
            timeout=30.0,
            verify=False,  # todo: check what to do with the certificate
        )

        response.raise_for_status()

        # Return the response as TokenResponse
        return TokenResponse.model_validate(response.json())

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request to OAuth server timed out")
    except requests.exceptions.HTTPError as e:
        # Handle 4xx/5xx HTTP status codes from OAuth server
        status_code = e.response.status_code if e.response else 502
        raise HTTPException(
            status_code=status_code, detail=f"OAuth server returned error: {str(e)}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502, detail=f"Error connecting to OAuth server: {str(e)}"
        )
    except (ValueError, ValidationError) as e:
        # Handle JSON parsing errors
        raise HTTPException(
            status_code=502, detail=f"Invalid response from OAuth server: {str(e)}"
        )

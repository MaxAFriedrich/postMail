# HTTP Form Submission Server

This project is a basic HTTP server written in Python that listens for POST requests on specified URLs, validates the
form data, sends an email with the form data, and redirects the client based on the validation result.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/MaxAFriedrich/postMail.git
    cd postMail
    ```

2. Install the required Python packages:
    ```sh
    pip install pyyaml
    ```
   Or use poetry:
    ```sh
    poetry install
    ```

## Configuration

1. Create a `config.yml` file in the project root directory with the following structure, (see `config.example.yml`):
    ```yaml
    sender_login: "your_login@example.com"
    sender_email: "your_email@example.com"
    sender_password: "your_password"
    smtp_server: "smtp.example.com"
    smtp_port: 587
    submission_points:
      - submission_url: "/abc"
        success_url: "http://example.com/success"
        error_url: "http://example.com/error"
        subject: "Form Submission"
        to_email: "recipient@example.com"
    ```

2. Update the configuration file with your email credentials and submission points.

## Usage

1. Run the server:
    ```sh
    python server.py
    ```
    Or use poetry:
     ```sh
    poetry run python server.py
    ```

2. Send a POST request to the server using `curl`:
    ```sh
    curl -X POST http://localhost:8080/abc -d "name=JohnDoe&email=johndoe@example.com"
    ```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

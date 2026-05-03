# Delta specifications for login 

### propuse 

- dynamic and customisable authentication method such like the authentication packages / SSP of windows 
- posibility to change of operator 
- Hexagonal architecture 

the repository should expedit a token witch will use the follow architecture

user.roles.id.auth

the auth module should work independly of the echo maze DAO so it should use their own repository but 

user storie 1: as operator i need a method wich will act as a form of change of operator at the activation of the UI 
user storie 2: as software architecture i need a structure wich supports diferent authentication methods 

user storie 2: as operator i need to login using diferent authenticatrion methods such as 
password or auth0


### work

  Key Achievements:
   1. Hexagonal Architecture Refactoring: Cleaned up the existing skeleton in the auth/ directory, fixing syntax errors and properly defining Ports (interfaces) and Adapters (implementations).
   2. Domain Implementation:
       * User & Token: Implemented the User dataclass and a Token model that follows the required format: user.roles.id.auth.
       * Authentication Logic: The IAM service now orchestrates the login process using interchangeable IAuthenticatorProvider strategies.
   3. Flexible Adapters:
       * Implemented a PasswordAuthenticator as a default authentication method.
       * Created an InMemoryUserRepository to manage operator data independently of the main database.
   4. Session Management: Added a SessionManager to track the current operator's session and token.
   5. CLI Integration:
       * Updated launch.py to include a --login flag.
       * Integrated a mandatory login prompt when starting the UI (--ui), fulfilling the user story for operator authentication at UI activation.
   6. Verification: Developed a comprehensive test suite in test/test_auth.py, confirming successful login flows, failed attempts, and correct token encoding.

  How to use:
   * Run with login: python launch.py --login
   * Start UI (will prompt for login): python launch.py --ui
   * Run Auth Tests: $env:PYTHONPATH="."; python test/test_auth.py

  Default credentials: admin / admin.


### proposes login 
  1. Flujo de Inicialización Interactiva (Bootstrap)
  Modificar el proceso de primera ejecución para que, en lugar de crear automáticamente la cuenta
  admin:admin, el sistema detecte que no hay usuarios y solicite interactivamente al operador
  configurar la contraseña del administrador principal. Esto se integraría en el comando --init-db.

  2. Política de "Forced Password Reset"
  Implementar un flag requires_password_change en el modelo de usuario.
   * Lógica: Si el IAM detecta un inicio de sesión con una contraseña marcada como "temporal" o "por
     defecto", el token devuelto incluirá un estado de "Restricción".
   * Acción: El launch.py bloqueará el acceso a la TUI y a otros comandos hasta que se complete
     exitosamente una función de cambio de contraseña.

  3. Integración con el Motor de Scoring OPSEC
  Dado que EchoMaze ya tiene un sistema de puntuación de ruido y sigilo (OPSEC), propongo:
   * Penalización: Si la cuenta de administrador por defecto sigue activa con la configuración base,
     el ScoringEngine aplicará una penalización severa al "Sigilo del Operador", ya que tener
     credenciales débiles es una vulnerabilidad crítica en una operación de pentest.
   * Advertencia en TUI: Mostrar un banner de alta visibilidad en la interfaz de asciimatics mientras
     las credenciales no sean seguras.

  4. Rotación Automática de Clave de Firma
  Como el repositorio ahora usa el hash del admin para firmar tokens, forzar el cambio de contraseña
  obligará al sistema a re-firmar la base de datos de usuarios con una nueva clave derivada de la
  contraseña segura, asegurando que el "secreto" del sistema no sea conocido por defecto.
  
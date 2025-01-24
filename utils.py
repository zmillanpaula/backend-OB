def login_to_campus(driver, username, password):
    driver.get("https://campusvirtual.bestwork.cl/login/index.php")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "loginbtn"))).click()

    # Verificar login exitoso
    if "login" in driver.current_url:
        raise Exception("Login failed. Invalid credentials.")
    return driver
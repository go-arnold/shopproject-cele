try:
    a = int(input("Enter a number : "))
    if a % 2 == 0:
        print(f"{a} is divisble by two")
    else:
        print(f"{a} is not divisible by 2")
except:
    print("Ony numbers are accepted")

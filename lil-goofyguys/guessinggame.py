#generate random number, ask for guess, return high or low,
#track number of guesses, end on correct guess
import random

winner = random.randint(1,10)
tries = 0
guess = int(input('Pick a number between 1 and 10 '))
while winner != guess:
    if guess < winner:
        guess = int(input('Too low! Try again. '))
    else:
        guess = int(input('Too high! Try again. '))
    tries = tries + 1
print('GG, the answer was ', winner, ' and you tried ', tries, ' time(s)!')

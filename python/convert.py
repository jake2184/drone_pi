

# Converts a number into a float representation
# Due to tricky format of Mavlink
def convert(number):
    number = int(number)
    number = "{0:b}".format(number)
    number = number.zfill(32)

    sign = pow(-1, int(number[0]))
   #print (sign)

    index = 8
    expon = 0
    for x in range (0,7):
        expon += int(number[index]) * pow(2, x)
        index -= 1
    expon -= 127
    #print (expon)



    index = 9
    manti = 1
    for x in range (1, 24):
        manti += int(number[index]) * pow(2, -x)
        index += 1
    #print (manti)

    toRet = 0
    if expon == -127:
        toRet = sign * pow(2, expon+1) * (manti-1)
    else:
        toRet = sign * pow(2, expon) * manti

    #print(toRet)
    return toRet

if __name__ == '__main__':
    p = 5
    num = "{0:b}".format(p)
    print(num.zfill(32))
    convert(num.zfill(32))
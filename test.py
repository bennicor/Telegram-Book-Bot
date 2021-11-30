# num = 5

# # Square
# print("\n".join(["*" * num for i in range(num)]))
# print()

# # Triangle
# print("\n".join(["*" * (i + 1) for i in range(num)]))
# print()

# # Upside down triangle
# print("\n".join(["*" * (num - i) for i in range(num)]))
# print()

# # Pyramid
# print("\n".join([("* " * (i + 1)).rjust(num * 2 + i) for i in range(num)]))
# print()

# print("".join([((" * " if n < 15 else " * \n") if (int(c, 16) & (1 << n)) else ("   " if n < 15 else "   \n")) for c in ["36", "49", "41", "22", "14", "8"] for n in range(16)]))
# print('\n'.join(' '.join(*zip(*row)) for row in ([["*" if row==0 and col%3!=0 or row==1 and col%3==0 or row-col==2 or row+col==8 else " " for col in range(7)] for row in range(6)])))

print("https://aldebaran.ru/author/goncharov_ivan/kniga_oblomov1859_ru/download.epub".split("/"))
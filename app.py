from flask import Flask, render_template, request, jsonify  # นำเข้าโมดูล Flask และเครื่องมือที่จำเป็น
import random  # ใช้สำหรับสุ่มตำแหน่ง
import copy    # ใช้สำหรับทำสำเนากระดาน

app = Flask(__name__)  # สร้างแอป Flask

# สร้างกระดานเปล่าขนาด 5x5 โดยกำหนดให้แต่ละช่องเป็น " "
board = [[" "]*5 for _ in range(5)]

# โหมดเกมเริ่มต้นคือ Player vs AI
game_mode = "PvAI"

def check_winner(board, player):
    """ ตรวจสอบว่าผู้เล่นชนะหรือไม่ (ต้องเรียงให้ได้ 4 ตัวติดกันในแนวใดแนวหนึ่ง) """
    for i in range(5):
        for j in range(2):  # ตรวจแนวนอน และแนวตั้ง
            if all(board[i][j+k] == player for k in range(4)): return True  # แนวนอน
            if all(board[j+k][i] == player for k in range(4)): return True  # แนวตั้ง

    for i in range(2):
        for j in range(2):  # ตรวจแนวเฉียง
            if all(board[i+k][j+k] == player for k in range(4)): return True  # เฉียงซ้ายบน-ขวาล่าง
            if all(board[i+3-k][j+k] == player for k in range(4)): return True  # เฉียงขวาบน-ซ้ายล่าง

    return False  # ถ้าไม่เข้าเงื่อนไขด้านบน แปลว่ายังไม่มีผู้ชนะ

def is_full(board):
    """ ตรวจสอบว่ากระดานเต็มหรือยัง """
    return all(cell != " " for row in board for cell in row)

def get_possible_moves(board):
    """ คืนค่าตำแหน่งที่ยังว่างในกระดาน """
    return [(i, j) for i in range(5) for j in range(5) if board[i][j] == " "]

def mcts_simulation(board, player):
    """ ใช้เทคนิค Monte Carlo Tree Search เพื่อหาการเดินที่ดีที่สุดให้ AI """
    simulations = 100  # จำนวนครั้งในการจำลองเกม
    moves = get_possible_moves(board)  # หาตำแหน่งที่ยังสามารถเดินได้
    if not moves:
        return None  # ถ้าไม่มีที่ว่างให้เดินเลย

    scores = {move: 0 for move in moves}  # เตรียม dictionary สำหรับเก็บคะแนนของแต่ละ move

    for move in moves:
        for _ in range(simulations):  # จำลองหลายๆ ครั้งเพื่อประเมินว่าการเดินนี้ดีไหม
            temp_board = copy.deepcopy(board)  # ทำสำเนากระดานเพื่อไม่ให้กระทบของจริง
            temp_board[move[0]][move[1]] = player  # ลงหมากที่ move นี้
            temp_player = "X" if player == "O" else "O"  # เปลี่ยนเทิร์น

            while not is_full(temp_board):
                if check_winner(temp_board, player):  # ถ้าผู้เล่นที่เริ่มชนะในการจำลองนี้
                    scores[move] += 1  # บวกคะแนนให้ move นี้
                    break
                # ถ้ายังไม่มีผู้ชนะ ให้สุ่มเดินต่อไป
                random_move = random.choice(get_possible_moves(temp_board))
                temp_board[random_move[0]][random_move[1]] = temp_player
                temp_player = "X" if temp_player == "O" else "O"  # สลับเทิร์น

    # หาการเดินที่มีคะแนนดีที่สุด
    best_move = max(scores, key=scores.get)
    return best_move

@app.route("/")
def index():
    return render_template("index.html")  # แสดงหน้า HTML หลักของเกม

@app.route("/move", methods=["POST"])
def move():
    global board, game_mode
    data = request.json  # รับข้อมูลจากฝั่ง client
    row, col = data["row"], data["col"]  # ดึงตำแหน่งที่ผู้เล่นเลือก

    # ถ้าช่องนี้มีคนเดินไปแล้ว
    if board[row][col] != " ":
        return jsonify({"error": "ตำแหน่งถูกใช้ไปแล้ว!"}), 400

    board[row][col] = "X"  # ผู้เล่นเป็น X

    if check_winner(board, "X"):
        return jsonify({"winner": "X", "board": board})  # ถ้าชนะก็ส่งผลกลับ
    if is_full(board):
        return jsonify({"winner": "draw", "board": board})  # ถ้าเสมอ

    # ถ้าโหมดคือเล่นกับ AI
    if game_mode == "PvAI":
        ai_move = mcts_simulation(board, "O")  # ให้ AI คิดว่าจะเดินจุดไหน
        if ai_move:
            board[ai_move[0]][ai_move[1]] = "O"  # ลงหมากให้ AI

        if check_winner(board, "O"):
            return jsonify({"winner": "O", "board": board})  # ถ้า AI ชนะก็ส่งผลกลับ

    return jsonify({"board": board})  # ถ้ายังไม่จบเกมก็อัปเดตกระดาน

@app.route("/set_mode", methods=["POST"])
def set_mode():
    global game_mode
    data = request.json
    game_mode = data["mode"]  # เปลี่ยนโหมดเกมจากคำสั่งฝั่ง client
    return jsonify({"mode": game_mode})

@app.route("/reset", methods=["POST"])
def reset():
    global board
    board = [[" "]*5 for _ in range(5)]  # สร้างกระดานใหม่
    return jsonify({"board": board})

if __name__ == "__main__":
    app.run(debug=True)  # เริ่มรัน Flask แอป

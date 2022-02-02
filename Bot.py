'''
Made by Brandon Ou
Last edited: 7/15/2021
Anarchychessvision Reddit Reply Bot

Acts as the chess ai for r/AnarchyChess posts by automatically evaluating positions after en passant (when possible).

Thanks to: reddit.com/u/pkacprzak. This would not have been possible without them.

Other features to add:
- Ability to play a move that forces en passant

'''
import praw  # Reddit API
import re  # regex
import chess
from chess import engine
from chess.engine import Cp

# Copy of original stockfish can be found at https://github.com/official-stockfish
# redirect uri is "http://localhost
# instance of reddit

reddit = praw.Reddit(
    client_id="8S6qonDBd6EBlu04YBmo5w",
    client_secret="rnlL5CVPUv5QpT-OwQDRV1ZahhyFqA",
    user_agent="<console:anarchychessvision-ai:1.0",
    username="anarchychessvision",
    password="enpassant"
)
'''
Algorithm:

Search through [some number] of AnarchyChess posts
    If there exists a post that chessvision-ai-bot has posted to and this bot has not
        See if en passant is allowed. If so, play en passant (this code may not work if there are 2 possible en passants)
        Evaluate the position (with stockfish) after en passant and post the result as a comment
'''

# name of chessvision-ai-bot to search for
botName = "chessvision-ai-bot"
# name of self
selfName = "anarchychessvision"
# Number of posts to scan
postlimit = 100
# Text in case of a stalemate
# >!...!< allows for spoilers
stalemateText = "I analyzed the image and this is what I see. \n\nEvaluation: >!The position is a stalemate!<"
# name of subreddit to search through
subreddit = reddit.subreddit("AnarchyChess")

# loop through top posts
for post in subreddit.new(limit=postlimit):
    # Flag determines if this bot has already commented (avoid repetition)
    # Could be replaced with a dictionary
    flag = False
    # Search through all comments to find if this bot has already commented
    for comment in post.comments:
        if comment.author == selfName:
            flag = True

    # Search through all comments to find if chessvision-ai-bot has already posted (html of that bot's comments has FEN)
    for comment in post.comments:
        if comment.author == botName and not flag:
            # print(comment.body_html)
            # html of comment -> use this to find the lichess analysis link
            html = comment.body_html

            # Format: lichess.org/analysis/<insertlink>
            # Regex to find the FEN with underscores instead of spaces
            link = re.search("lichess.*\"", html)

            # In case regex does not work or does not find anything
            if link is None:
                break
            else:
                # Truncate the link to just the FEN
                link = ((link.group(0))[: -1])[21:]

            # Converts link's FEN into actual FEN (replace underscores with spaces)
            actualFEN = link.replace("_", " ")
            # print(actualFEN)
            # Creates the chess board; breaks if can't happen
            try:
                board = chess.Board(actualFEN)  ######### Chess Board Here
            except:
                break
            # FEN is split into various sections
            # Removes underscores and separates the FEN into the board's FEN and the other info
            tempFen = link.split("_")
            # Split the board FEN into squares
            pieces = tempFen[0].split("/")
            beforeFen = pieces + tempFen[1:]

            # Finds the square in which en passant is allowed
            squareToEnPassant = beforeFen[10]


            # Analyses the board and returns an eval from the perspective of white
            def eval():
                chessEngine = chess.engine.SimpleEngine.popen_uci(
                    "stockfish_14_win_x64_popcnt\stockfish_14_win_x64_popcnt\stockfish_14_x64_popcnt.exe")
                score = chessEngine.analyse(board, chess.engine.Limit(time=10))
                # print(score)
                return score['score'].pov(chess.WHITE)

            if board.has_legal_en_passant():
                file = squareToEnPassant[0]  # a-h
                rank = squareToEnPassant[1]  # 1-8

                if rank == "6":
                    # it is white's turn
                    if file == "a":
                        board.push_uci("b5a6")
                    elif file == "h":
                        board.push_uci("g5h6")
                    else:
                        # en passant is with b-g pawn => 2 potential en passants
                        m1 = chess.Move(chess.parse_square(chr((ord(file) - 1)) + chr((ord(rank) - 1))),
                                        chess.parse_square(squareToEnPassant))
                        m2 = chess.Move(chess.parse_square(chr((ord(file) + 1)) + chr((ord(rank) - 1))),
                                        chess.parse_square(squareToEnPassant))
                        # try both en passants, m1 before m2
                        # will not be correct everytime, but it is a rare case
                        if m1 in board.legal_moves:
                            board.push_uci(board.uci(m1))
                        elif m2 in board.legal_moves:
                            board.push_uci(board.uci(m2))
                        else:
                            # Comment stalemate
                            post.reply(stalemateText)
                            break

                # Repeated for black
                else:
                    # it is black's turn
                    if file == "a":
                        board.push_uci("b4a3")
                    elif file == "h":
                        board.push_uci("g4h3")
                    else:
                        # en passant is with b-g pawn => 2 potential en passants
                        m1 = chess.Move(chess.parse_square(chr((ord(file) - 1)) + chr((ord(rank) + 1))),
                                        chess.parse_square(squareToEnPassant))
                        m2 = chess.Move(chess.parse_square(chr((ord(file) + 1)) + chr((ord(rank) + 1))),
                                        chess.parse_square(squareToEnPassant))
                        if m1 in board.legal_moves:
                            board.push_uci(board.uci(m1))
                        elif m2 in board.legal_moves:
                            board.push_uci(board.uci(m2))
                        else:
                            post.reply(stalemateText)
                            break

                # Since en passant has happened, find the engine evaluation

                score = eval()

                # Basic evaluation text
                evalText = "I analyzed the image and this is what I see. \n\nEvaluation: >!En passant was forced."
                # Convert the engine evaluation into a float with 2 decimal places
                if chess.engine.Score.is_mate(score):
                    if board.turn == chess.WHITE:
                        post.reply(">!Black has mate soon. I'm too lazy to calculate how many moves it'll take.!<")
                    else:
                        post.reply(">!White has mate soon. I'm too lazy to calculate how many moves it'll take.!<")
                    break

                score = float(Cp.score(score)) / 100.00
                scoreText = str(round(score, 2))

                # output text depends on evaluation
                if score >= 1:
                    post.reply(evalText + "White has the advantage +" + scoreText + " !<")
                elif score <= -1:
                    post.reply(evalText + "Black has the advantage " + scoreText + " !<")
                else:
                    post.reply(evalText + "The game is about equal " + scoreText + " !<")
                # If score is printed, a post was made.
                print(score)

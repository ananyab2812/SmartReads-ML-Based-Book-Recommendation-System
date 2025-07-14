from flask import Flask, render_template, request
import pickle
import numpy as np
from fuzzywuzzy import process  # For fuzzy matching

# Load data
popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

app = Flask(__name__)

@app.route('/')
def index():
    query = request.args.get('q', '')  # Get search query
    min_rating = request.args.get('min_rating', 0, type=float)  # Get min rating

    filtered_df = popular_df.copy()

    # Filter by search text (book title or author)
    if query:
        filtered_df = filtered_df[
            filtered_df['Book-Title'].str.contains(query, case=False, na=False) |
            filtered_df['Book-Author'].str.contains(query, case=False, na=False)
        ]

    # Filter by minimum rating
    filtered_df = filtered_df[filtered_df['avg_ratings'] >= min_rating]

    return render_template('index.html',
                           book_name=list(filtered_df['Book-Title'].values),
                           author=list(filtered_df['Book-Author'].values),
                           image=list(filtered_df['Image-URL-M'].values),
                           votes=list(filtered_df['num_ratings'].values),
                           rating=list(filtered_df['avg_ratings'].round(2).values),
                           query=query,
                           min_rating=min_rating
                           )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books', methods=['POST'])
def recommend():
    user_input = request.form.get('user_input')

    # Fuzzy matching to get the closest matching title from pt.index
    all_titles = pt.index.tolist()
    matched_title, match_score = process.extractOne(user_input, all_titles)

    if match_score < 60:
        return render_template('recommend.html', data=[], error="No close match found. Please try another title.")

    index = np.where(pt.index == matched_title)[0][0]
    similar_items = sorted(
        list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True
    )[1:6]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))
        data.append(item)

    return render_template('recommend.html', data=data, matched_title=matched_title)

if __name__ == '__main__':
    app.run(port=5001, debug=True)

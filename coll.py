from flask import Flask, jsonify
from pymongo import MongoClient
import numpy as np
from scipy.sparse.linalg import svds

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb+srv://shiraz:7TACxQM8U7RQE7ef@law4everyonecluster.mb609.mongodb.net/?retryWrites=true&w=majority')
db = client['test']
blogCollection = db['blogs']
userCollection = db['users']

@app.route('/')
def index():
    return 'Hello, Flask!'

@app.route('/predictBlogs')
def get_blogs():
    try:
        # Fetch blogs from MongoDB with title and description
        blogs = list(blogCollection.find({}, {"_id": 1, "title": 1, "description": 1}))
        # Fetch users from MongoDB with userName and their interactions (e.g., likes, views)
        users = list(userCollection.find({}, {"_id": 1}))

        if blogs and users:
            # Create user-item interaction matrix
            num_users = len(users)
            num_blogs = len(blogs)
            interactions_matrix = np.zeros((num_users, num_blogs))

            for user_idx, user in enumerate(users):
                user_id = user['_id']
                user_interactions = fetch_user_interactions(user_id)
                for blog_interaction in user_interactions:
                    blog_idx = blog_interaction['_id']
                    interactions_matrix[user_idx, blog_idx] = 1  # Assuming binary interaction (e.g., user viewed the blog)

            # Perform Singular Value Decomposition (SVD)
            U, sigma, Vt = svds(interactions_matrix, k=min(num_users, num_blogs) - 1)

            # Predict user-item interactions
            all_user_predicted_interactions = np.dot(np.dot(U, np.diag(sigma)), Vt)

            # Recommend top blogs for each user
            recommended_blogs = {}
            for user_idx, user in enumerate(users):
                user_id = str(user['_id'])  # Convert ObjectId to string
                user_predicted_interactions = all_user_predicted_interactions[user_idx, :]
                sorted_blog_indices = np.argsort(user_predicted_interactions)[::-1]

                recommended_blogs[user_id] = []
                for blog_idx in sorted_blog_indices:
                    blog_info = blogs[blog_idx]
                    recommended_blogs[user_id].append({'blog_id': str(blog_info['_id']), 'title': blog_info['title'], 'description': blog_info['description']})

            return jsonify(recommended_blogs)
        else:
            return jsonify({'message': 'No blogs or users found'})
    except Exception as e:
        return jsonify({'error': str(e)})

def fetch_user_interactions(user_id):
    # Fetch user interactions (e.g., likes, views) from MongoDB
    # Example implementation:
    interactions = userCollection.find_one({'_id': user_id}, {'interactions': 1})
    return interactions.get('interactions', [])

if __name__ == '__main__':
    app.run(debug=True)

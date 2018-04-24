import os
import argparse
from gensim.models import Word2Vec
import multiprocessing as mp

model = None
test_files = [
				'test/seen/test.txt',
				'test/seen/random.txt',
				'test/missing/test.txt',
				'test/missing/random.txt'
          	 ]


def compute_sim(authors):
	similarity = model.wv.similarity(authors[0], authors[1])
	return (authors[0], authors[1], similarity)


def compute_similarities(model_file, num_threads):
	global model
	model = Word2Vec.load(model_file)
	authors_train = [author for author in model.wv.vocab]

	authors_test = set()
	pool = mp.Pool(num_threads)
	for test_file in test_files:
		print('Computing similarities for file: ', test_file)
		author_edges = []
		lines = open(test_file)
		for line in lines:
			authors = line.strip().split()
			authors_test.add(authors[0])
			authors_test.add(authors[1])
			
			if authors[0] not in model.wv.vocab:
				continue
			if authors[1] not in model.wv.vocab:
				continue
			
			author_edges.append((authors[0], authors[1]))

		scores = ''
		author_edges_scores = pool.map(compute_sim, author_edges)
		for z in author_edges_scores:
			scores += z[0] + ' ' + z[1] + ' ' + str(z[2]) + '\n'

		filename = 'test_scores/scores_' + model_file[model_file.rfind('model_') + 6: model_file.rfind('.bin')] + test_file[4:]
		os.makedirs(os.path.dirname(filename), exist_ok=True)
		with open(filename, 'w') as f:
			f.write(scores)

	print('Number of authors in train: ', len(authors_train))
	print('Number of authors in test: ', len(authors_test))


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Compute cosine similarities of edges in test data. File as saved in the folder "test_scores".')
	parser.add_argument('-f','--model_file', dest='model_file', required=True,
			    help='File containing author embeddings(REQUIRED)')
	parser.add_argument('-t','--num_threads', dest='num_threads', default=44,
			    help='Number of threads used for parallelization(default: 44)')

	args = parser.parse_args()

	compute_similarities(model_file=args.model_file, num_threads=int(args.num_threads))
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
const schema = require('../models/user.model.js');
// schema.Cred --> CredentialsSchema
// schema.Stat --> StatsSchema
// schema.Hist --> HistorySchema
// schema.User --> UserSchema


// verify that user-provided username is unique
exports.isUniqueUsername = (req,res) => {
	const info = req.body;
	// validate request
	if(!info.username) {
		return res.status(400).json({
			status: "failure",
			error: "a username was not provided"
		});
	}
	schema.User.findOne({'credentials.username': info.username})
	.then(exists => {
		if(!exists) {
			return res.json({
				status: "success"
			});
		} else {
			return res.json({
				status: "failure",
				error: "the username provided is already taken"
			});
		}
	}).catch(err => {
		return res.status(500).json({
			status: "failure",
			error: err.message || "error retrieving information from the database"
		});
	});
};

// user sign-up, store basic sign-up information 
exports.signUp = (req,res) => {
	const info = req.body;
	// validate request
	if(!info.firstName || !info.lastName || !info.email || !info.username || !info.password) {
		return res.status(400).json({
			status: "failure",
			error: "some or all required fields were not provided"
		});
	}

	schema.User.findOne({'credentials.emailAddress': info.email})
	.then(exists => {
		if(exists) {
			return res.status(400).json({
				status: "failure",
				error: "an account with the user-provided email address already exists"
			});
		} else {
			// create a new user
			const cred = new schema.Cred({
				emailAddress: info.email,
				username: info.username,
				password: info.password
			});
			const user_s = new schema.User({
				firstName: info.firstName,
				lastName: info.lastName,
				credentials: cred,
				lastLogin: Date("<YYYY-mm-ddTHH:MM:ss>"),
				gameHistory: []
			});
			// store user information in the database 
			user_s.save()
			.then(data => {
				return res.json({
					status: "success",
					info: data
				});
			}).catch(err => {
				return res.status(500).json({
					status: "failure",
					error: err.message || "error occured while storing information in the database"
				});
			});
		}
	}).catch(err => {
		return res.status(500).json({
			status: "failure",
			error: err.message || "error retrieving information from the database"
		});
	});
};

// user sign-in, verify that user-provided username/email exists and check password
exports.signIn = (req,res) => {
	const info = req.body;
	// validate request
	if(!info.user && !info.password) {
		return res.status(400).json({
			status: "failure",
			error: "username or password was not provided"
		});
	}
	// build query based on whether the user signed-in with email or username
	if((info.user).includes("@")) {
		// res.setHeader('type', 'emailAddress');
		var query = schema.User.findOne({'credentials.emailAddress': info.user});
	} else {
		// res.setHeader('type', 'username');
		var query = schema.User.findOne({'credentials.username': info.user});
	}
	query.exec(function(err,doc) {
		if(err) {
			return res.status(500).json({
				status: "failure",
				error: err.message || "error occured when retrieving information from the database"
			});
		}
		// compare user-provided password with the hashed password from db, doc.credentials.password
		bcrypt.compare(info.password,doc.credentials.password,function(err,result) {
			if(err) {
				return res.status(500).json({
					status: "failure",
					error: err.message || "error occured when comparing passwords"
				});
			}
			if(result == true) {
				doc.lastLogin = Date("<YYYY-mm-ddTHH:MM:ss>");
				doc.save();
				return res.json({
					status: "success",
					info: result
				});
			} else {
				return res.json({
					status: "failure",
					error: "user-provided password does not match"
				});
			}
		});
	});
};

// initialize game
exports.initializeGame = (req,res) => {
	const info = req.body;
	// validate request
	if(!info.username || !info.netflixWatchID) {
		return res.status(400).json({
			status: "failure",
			error: "a username or contentID was not provided"
		});
	}
	// check if gameID exists for the username and netflixWatchID
	schema.User.findOne({'credentials.username': info.username, 'gameHistory.netflixWatchID': info.netflixWatchID}, {'gameHistory': {$elemMatch: {'netflixWatchID': info.netflixWatchID, 'completed': false}}})
	.then(doc => {
		if(doc) {
		// if a gameHistory document DOES already exist for the specified username and netflixWatchID
			return res.json({
				status: "success",
				gameID: doc.gameHistory[0]._id,
				resuming: true
			});
		} else { 
		// if a gameHistory document DOES NOT already exist for the specified username and netflixWatchID
			schema.User.findOne({'credentials.username': info.username})
			.then(result => {
				const scores = new schema.Score({
					scores: {},
					dialogueIDs: []
				});
				const history = new schema.Hist({
					netflixWatchID: info.netflixWatchID,
					completed: false,
					activity: Date("<YYYY-mm-ddTHH:MM:ss>"),
					scores: scores
				});
				// save data in gameHistory field array
				result.gameHistory.push(history);
				result.save()
				.then(data => {
					return res.json({
						status: "success",
						gameID: data.gameHistory[0]._id,
						resuming: false
					});
				}).catch(err => {
					return res.status(500).json({
						status: "failure",
						error: err.message || "error occured when saving user game data into database"
					});
				});
			}).catch(err => {
				return res.status(500).json({
					status: "failure",
					error: err.message || "error retrieving information from the database"
				});
			});
		}
	}).catch(err => {
		return res.status(500).json({
			status: "failure",
			error: err.message || "error retrieving information from the database"
		});
	})
};

// store user score data
exports.storeScoreData = (req,res) => {
	const info = req.body;
	// validate request
	if(!info.gameID) {
		return res.status(400).json({
			status: "failure",
			error: "gameID was not provided"
		});
	}
	// find the user's game document connected to the given gameID and store/update data
	schema.User.findOne({/* 'credentials.username': info.username,  */'gameHistory._id': mongoose.Types.ObjectId(info.gameID)})
	.then(doc => {
		if(doc) {

			doc.gameHistory.id(mongoose.Types.ObjectId(info.gameID)).scores.scores.set(info.dialogueID.toString(), {'phoneticScore': info.phoneticScore, 'lyricalScore': info.lyricalScore, 'emotionScore': info.emotionScore, 'averageScore': info.averageScore});
			doc.gameHistory.id(mongoose.Types.ObjectId(info.gameID)).scores.dialogueIDs.push(info.dialogueID);

			doc.save()
			.then(result => {
				return res.json({
					status: "success"
				});
			}).catch(err => {
				// return res.status(500).json({
				console.log("(contentDB) here1")
				return res.json({
					status: "failure",
					error: err.message || "error occured when storing score data in the database"
				});
			});
		}
		else {
			// console.log("(userDB) here2");
			return res.json({
				status: "failure",
				error: "could not find gameID " + info.gameID
			})
		}
	}).catch(err => {
		// return res.status(500).json({
		// console.log("(contentDB) here3")
		return res.json({
			status: "failure",
			error: err.message || "error retrieving information from the database"
		});
	});
};

// close game and set 'completed' field to true
exports.closeGame = (req,res) => {
	const info = req.body;
	// validate request
	if(info.reqType!='closeGame' || !info.gameID) {
		return req.status(400).json({
			status: "failure",
			error: err.message || "reqType not closeGame or gameID not provided"
		});
	}
	schema.User.findOne({'gameHistory._id': mongoose.Types.ObjectId(info.gameID)})
	.then(doc => {
		doc.gameHistory.id(mongoose.Types.ObjectId(info.gameID)).completed=true;
		doc.save()
		.then(data => {
			return res.json({
				status: "success"
			});
		}).catch(err => {
			return res.status(500).json({
				status: "failure",
				error: err.message || "error occured when updating document"
			});
		});
	}).catch(err => {
		return res.status(500).json({
			status: "failure",
			error: err.message || "error retrieving information from the database"
		});
	});
};
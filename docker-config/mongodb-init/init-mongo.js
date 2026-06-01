db = db.getSiblingDB('admin');

// Create admin user if it doesn't exist
if (!db.getUser(process.env.MONGO_INITDB_ROOT_USERNAME)) {
    db.createUser({
        user: process.env.MONGO_INITDB_ROOT_USERNAME,
        pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
        roles: ["root"]
    });
}

db.auth(process.env.MONGO_INITDB_ROOT_USERNAME, process.env.MONGO_INITDB_ROOT_PASSWORD);

// Switch to application database
db = db.getSiblingDB(process.env.MONGO_APP_DATABASE);

// Create application user if it doesn't exist
if (!db.getUser(process.env.MONGO_APP_USER)) {
    db.createUser({
        user: process.env.MONGO_APP_USER,
        pwd: process.env.MONGO_APP_PASSWORD,
        roles: [
            { role: "readWrite", db: process.env.MONGO_APP_DATABASE }
        ]
    });
    print("Created application user " + process.env.MONGO_APP_USER + " for database " + process.env.MONGO_APP_DATABASE);
} 
# Final-Year-Project-Secure-File-Sharing

A website to store and view files. To be used by corporations, hence it has different levels of user(Staff, Manager, Director). It has a mixture of Role-based access control and User-based access control.

How it works: 

When a file is uploaded, it is divided equally into 3 parts. Website is connected to 3 cloud providers. Each part is then stored in a different cloud provider. This ensures that no cloud provider holds the original file.

When a user wants to view a file, the 3 files is then merged back into one to be viewed. 

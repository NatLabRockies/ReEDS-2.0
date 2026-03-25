# Some good instances
#	m5a.12xlarge	48	x86_64	192	-	-	10 Gigabit	2.064 USD per Hour
#   r5a.24xlarge	96	x86_64	768	-	-	20 Gigabit	5.424 USD per Hour

#general process
#GIT installation   
sudo yum -y install git
sudo amazon-linux-extras install epel
sudo yum -y install git-lfs
git lfs install

#Append two export commands for GAMS and conda to .bashrc:
echo "export GAMSDIR=/opt/gams/gams35.1_linux_x64_64_sfx" >> ~/.bashrc
echo "export PATH=/home/ec2-user/anaconda3/bin/:$PATH:/opt/gams/gams35.1_linux_x64_64_sfx/" >> ~/.bashrc

#if this is a new disk, you need to establish a file system
sudo mkfs -t xfs /dev/xvdo
# copy over the gams license file from your local machine to the gams system directory
# this directory was created in the last step and varies with the gams installation version
#!!!! this needs to be changed for each user - both the directory names and gams license file
#!!!! following command need to be run from local terminal any time you mount or create a new file system on a drive
#scp -i MB_R2.pem -r /Users/mbrown1/Desktop/gamslice.txt ec2-user@172.18.32.113:~/r2/gamslice.txt

#need to make a directory to mount that volume.. here just setting it up as ~/r2
sudo mkdir ~/r2
#then mount the directory to that folder:
#!!!! depends on what drive letter you assigned in ec2 web interface
#!!!! here i defined my drive as /dev/sdo
sudo mount /dev/sdo ~/r2	

#make sure you have ownership of the drive and the opt directory (where we'll install GAMS):
sudo chown -R ec2-user ~/r2
sudo chown -R ec2-user /opt
# make a directory for gams
mkdir /opt/gams
# change to that directory and download the gams installer
cd /opt/gams
#!!!! alternatively, this could be stored on your EBS drive and copied over
wget "https://d37drm4t2jghv5.cloudfront.net/distributions/35.1.0/linux/linux_x64_64_sfx.exe"

# change permissions for the installation file
chmod 755 linux_x64_64_sfx.exe 
# unpack the installation file
# not sure why the entire directory needs to spelled out here but it does...
/opt/gams/linux_x64_64_sfx.exe 

#copy over the gams license stored on your drive
cd gams35.1_linux_x64_64_sfx
nano ~/r2/gamslice.txt

#add license file contents

cp ~/r2/gamslice.txt gamslice.txt

#export GAMSDIR for GDXPDS
export GAMSDIR=/opt/gams/gams35.1_linux_x64_64_sfx

#installing anaconda
#following step only needs to be done if the installation file is not on your drive
cd ~/r2
#!!!! alternatively, this could be stored on your EBS drive 
wget "https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh"

#create a temporary directory given need to read/write from non-write-protected directory
mkdir ~/tmp
chown -R ec2-user ~/tmp 
#actual installation call
#note setting up the temporary directory for this call and putting installation files
# in the /home/ec2-user/anaconda3 directory - the 'b' and 'p' arguments make it silent 
# and indicate that the directory specified is the installation path
TMPDIR=~/tmp sh /home/ec2-user/r2/Anaconda3-2020.11-Linux-x86_64.sh -b -p /home/ec2-user/anaconda3

#ordering matters here - we want to be certain that 
#the system sees the conda version of python before
#any other - both GAMS and otherwise
export PATH=/home/ec2-user/anaconda3/bin/:$PATH:/opt/gams/gams35.1_linux_x64_64_sfx/

#make sure you have the appropriate packages installed
conda install pandas numpy scipy scikit-learn matplotlib networkx numba 
pip install gdxpds ticker

#------------------------
# -- git instructions -- 
#------------------------

ssh-keygen -t rsa -b 4096 -C "youremailaddress@nrel.gov"  
#ssh-keygen -t rsa -b 4096 -C "maxwell.brown@nrel.gov"  
eval "$(ssh-agent -s)"
ssh-add id_rsa
#[copy key and add to your github.nrel.gov account]
ssh -T git@github.nrel.gov
#type yes 
# should say Hi [username]! ...
git clone https://github.nrel.gov/ReEDS/ReEDS-2.0.git reeds

git clone git@github.nrel.gov:ReEDS/ReEDS-2.0


# Run ReEDS! 
# (using nohup to keep the process from dying when you end your ssh session)
#nohup python runbatch_aws.py -c weekendcentroid -r 4 -b centwknd > myout.txt &


#========================================
# -- old but potentially useful lines --
#========================================

#Following lines needed if using the gams version of python...
#these export path lines could all be wrapped together
#but it helps me to break them out to avoid one big line
#export PATH=$PATH:/opt/gams/gams35.1_linux_x64_64_sfx/
#following instructs to use the gams version of python
#allows us to avoid installing/configuring conda
#ordering matters here! - we want the system to 
#see the GAMS version of python first
#export PATH=/opt/gams/gams35.1_linux_x64_64_sfx/GMSPython:$PATH
#add python package directory for GAMS python to path:
#export PATH=$PATH:/opt/gams/gams35.1_linux_x64_64_sfx/GMSPython/bin
#can test to see if the following worked by typing:
#which python
#and should get something like:
#/opt/gams/gams35.1_linux_x64_64_sfx/GMSPython/python

#install necessary python packages
#sudo yum install git
#need to manually install a base package for python
#that is not included with the gams version for some reason
#and is not available via pip ----- such a headache
#i've contacted GAMS on this.. working on a solution
#git clone https://github.com/python/cpython.git
#cp -r cpython/Lib/unittest/ /opt/gams/gams35.1_linux_x64_64_sfx/GMSPython/lib/python3.8/site-packages/unittest/

#move to your git directory
#!!! could be different for different users
#cd ~/r2/r2_aws


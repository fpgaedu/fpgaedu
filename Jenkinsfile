# vi: set ft=groovy

pipeline {
    stages {
        stage('Init') { // for display purposes
            git 'https://github.com/fpgaedu/fpgaedu'
        }
        stage('Build') {
            steps {
                node('ubuntu&&16.04&&x64&&vivado&&webpack&&2016.4&&nexys4) {
                    echo 'hello ubuntu 16+vivado 2016.4 lab'
                }
                node('ubuntu&&16.04&&x64&&vivado&&lab&&2016.4&&nexys4) {
                    echo 'hello ubuntu 16+vivado 2016.4 lab'
                }
            }
        }
    }
}

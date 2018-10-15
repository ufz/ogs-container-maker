pipeline {
  options {
    buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '15'))
  }
  agent { label 'singularity' }
  parameters {
    // booleanParam(name: 'centos', defaultValue: true, description: 'ubuntu or centos')
    // string(name: 'repo', defaultValue: 'https://github.com/ufz/ogs', description: 'Git repository URL')
    // string(name: 'branch', defaultValue: 'master', description: 'Git repository branch')
    string(name: 'ogs', defaultValue: 'True False', description: 'Build OGS in container')
    string(name: 'format', defaultValue: 'docker singularity', description: 'Container format')
    string(name: 'openmpi_versions', defaultValue: 'off 2.1.1 2.1.5 3.0.1 3.1.2', description: 'OpenMPI versions')
  }
  stages {
    stage('Build') {
      steps {
        script {
          dir('scripts/container/generator') {
            sh """
              python3 -m venv ./venv
              . ./venv/bin/activate
              pip install --upgrade https://github.com/bilke/hpc-container-maker/archive/dev.zip

              ml singularity/2.6.0
              mkdir -p _gen
              python build.py --output _gen --format ${params.format} --ogs ${params.ogs} --ompi ${params.openmpi_versions} > _gen_script.sh
              bash _gen_script.sh
            """.stripIndent()
          }
        }
      }
    }
  }
  post {
    success {
      archiveArtifacts artifacts: 'scripts/container/generator/_gen/*.simg'
    }
    always {
      archiveArtifacts artifacts: 'scripts/container/generator/_gen/*.def'
    }
    cleanup { sh 'rm -rf scripts/container/generator/_gen*' }
  }
}

// Note: use input-step to deploy to HPC resource? https://stackoverflow.com/a/45216570/80480

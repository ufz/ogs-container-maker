pipeline {
  options {
    buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '15'))
  }
  agent { label 'singularity' }
  parameters {
    string(name: 'ogs', defaultValue: 'ufz/ogs@master',
           description: 'Build OGS in container (Github user/repo@branch)')
    string(name: 'format', defaultValue: 'docker singularity',
           description: 'Container format')
    string(name: 'openmpi_versions', defaultValue: 'off 2.1.1 2.1.5 3.0.1 3.1.2',
           description: 'OpenMPI versions')
    string(name: 'pm', defaultValue: 'conan spack',
           description: 'Package manager to install third-party libs')
    string(name: 'cmake', defaultValue: '',
           description: 'CMake args, use : instead of = , e.g. -DFOO:BAR')
  }
  stages {
    stage('Build') {
      steps {
        script {
          sh """
            python3 -m venv ./venv
            . ./venv/bin/activate
            pip install --upgrade \
              https://github.com/bilke/hpc-container-maker/archive/dev.zip
            ml singularity/2.6.0
            alias singularity=`which singularity`
            export PYTHONPATH="\$PYTHONPATH:./"
            python build.py --format ${params.format} \
              --ogs ${params.ogs} --ompi ${params.openmpi_versions} \
              --pm ${params.pm} --cmake_args '${params.cmake}'
          """.stripIndent()
        }
      }
    }
  }
  post {
    always {
      archiveArtifacts artifacts: '_out/**/*.simg,_out/**/*.def,_out/**/Dockerfile'
    }
    cleanup { sh 'rm -rf _out' }
  }
}

// Note: use input-step to deploy to HPC resource? https://stackoverflow.com/a/45216570/80480

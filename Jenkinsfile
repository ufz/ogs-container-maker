pipeline {
  options {
    buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '15'))
  }
  agent { label 'singularity' }
  parameters {
    booleanParam(name: 'singularity_via_docker', defaultValue: false, description: 'Build Docker, then convert to Singularity (maybe faster)')
    // string(name: 'repo', defaultValue: 'https://github.com/ufz/ogs', description: 'Git repository URL')
    // string(name: 'branch', defaultValue: 'master', description: 'Git repository branch')
    string(name: 'ogs', defaultValue: 'True False', description: 'Build OGS in container')
    string(name: 'format', defaultValue: 'docker singularity', description: 'Container format')
    string(name: 'openmpi_versions', defaultValue: 'off 2.1.1 2.1.5 3.0.1 3.1.2', description: 'OpenMPI versions')
    string(name: 'pm', defaultValue: 'conan spack', description: 'Package manager to install third-party libs')
    string(name: 'cmake', defaultValue: '', description: 'CMake args, use : instead of = , e.g. -DFOO:BAR')
  }
  stages {
    stage('Build') {
      steps {
        script {
          def script = "build.py"
          if(params.singularity_via_docker) {
            script = "spython_build.py"
          }
          sh """
            python3 -m venv ./venv
            . ./venv/bin/activate
            pip install --upgrade https://github.com/bilke/hpc-container-maker/archive/dev.zip
            ml singularity/2.6.0
            alias singularity=`which singularity`
            mkdir -p _gen
            python ${script} --output _gen --format ${params.format} --ogs ${params.ogs} --ompi ${params.openmpi_versions} --pm ${params.pm} --cmake_args '${params.cmake}'
          """.stripIndent()
        }
      }
    }
  }
  post {
    always {
      archiveArtifacts artifacts: '_gen/*.simg'
      archiveArtifacts artifacts: '_gen/*.def'
    }
    cleanup { sh 'rm -rf _gen*' }
  }
}

// Note: use input-step to deploy to HPC resource? https://stackoverflow.com/a/45216570/80480

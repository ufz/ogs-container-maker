pipeline {
  options {
    buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '15'))
  }
  agent { label 'singularity' }
  parameters {
    booleanParam(name: 'ogs', defaultValue: true, description: 'Build OGS, or just simple MPI tests')
    choice(choices: ['singularity', 'docker'], description: '', name: 'format')
    booleanParam(name: 'centos', defaultValue: true, description: 'ubuntu or centos')
    string(name: 'repo', defaultValue: 'https://github.com/ufz/ogs', description: 'Git repository URL')
    string(name: 'branch', defaultValue: 'master', description: 'Git repository branch')
    choice(choices: ['2.1.1', '2.1.3', '2.1.4', '3.0.2', '3.1.1'], description: '', name: 'openmpi_version')
    booleanParam(name: 'benchmarks', defaultValue: true, description: '')
    booleanParam(name: 'infiniband', defaultValue: true, description: '')
  }
  stages {
    stage('Build') {
      steps {
        script {
          def filename = params.format.capitalize()
          if (params.format == "docker") {
            filename += "file"
          }
          def config_string = "openmpi-${params.openmpi_version}"
          if (params.centos == true) {
            config_string = "centos-${config_string}"
          }
          else {
            config_string = "ubuntu-${config_string}"
          }
          if (params.ogs == false) {
            config_string = "test-${config_string}"
          }
          if (params.infiniband == false) {
            config_string = "${config_string}-no_infininband"
          }
          filename += ".${config_string}"
          dir('hpccm') {
            sh """
              python3 -m venv ../venv
              . ../venv/bin/activate
              pip install --upgrade six
              python ../hpc-container-maker/hpccm.py --recipe ogs-builder.py \
                --userarg ompi=${params.openmpi_version} \
                        centos=${params.centos} \
                        repo=${params.repo} \
                        branch=${params.branch} \
                        ogs=${params.ogs} \
                        benchmarks=${params.benchmarks} \
                        infiniband=${params.infiniband} \
              --format ${params.format} \
              > ${filename}
            """.stripIndent()
            sh "cat ${filename}"
            if (params.format == "docker") {
              sh "docker build -t ogs6/${config_string} -f ${filename} ."
            }
            else {
              sh """
                sudo singularity build ogs.${config_string}.simg ${filename}
                sudo chown jenkins ogs.${config_string}.simg
                singularity inspect ogs.${config_string}.simg > ogs.${config_string}.json
                singularity inspect --app ogs ./ogs.${config_string}.simg > ogs.${config_string}.scif.json
              """.stripIndent()
            }
          }
        }
      }
    }
  }
  post {
    success {
      archiveArtifacts artifacts: '**/*.simg,hpccm/**/*.json'
      script {
        currentBuild.displayName = "#${currentBuild.number}: ${params.repo} / ${params.branch}"
        currentBuild.description = """
          CentOS: ${params.centos}\n
          Container Format: ${params.format}\n
          OpenMPI: ${params.openmpi_version}
          """.stripIndent()
      }
    }
    always {
      archiveArtifacts artifacts: 'hpccm/**/Singularity.*,hpccm/**/Dockerfile.*'
    }
    cleanup { sh 'rm -rf hpccm/**/*.simg hpccm/**/Singularity.* hpccm/**/Dockerfile.*' }
  }
}

// Note: use input-step to deploy to HPC resource? https://stackoverflow.com/a/45216570/80480
